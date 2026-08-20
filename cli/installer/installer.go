package installer

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"os"
	"path"
	"strings"

	cp "github.com/otiai10/copy"
	"github.com/syncloud/golib/config"
	"github.com/syncloud/golib/linux"
	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

type Variables struct {
	App               string
	AppDir            string
	DataDir           string
	CommonDir         string
	Socket            string
	Url               string
	AuthLocalSocket   string
	NginxSyslogTag    string
	RegistrationToken string
}

const (
	App       = "fmd-server"
	AppDir    = "/snap/fmd-server/current"
	DataDir   = "/var/snap/fmd-server/current"
	CommonDir = "/var/snap/fmd-server/common"
)

type Installer struct {
	newVersionFile     string
	currentVersionFile string
	tokenFile          string
	platformClient     *platform.Client
	installFile        string
	logger             *zap.Logger
}

func New(logger *zap.Logger) *Installer {
	return &Installer{
		newVersionFile:     path.Join(AppDir, "version"),
		currentVersionFile: path.Join(DataDir, "version"),
		tokenFile:          path.Join(DataDir, "registration.token"),
		platformClient:     platform.New(),
		installFile:        path.Join(CommonDir, "installed"),
		logger:             logger,
	}
}

func (i *Installer) Install() error {
	return i.UpdateConfigs()
}

func (i *Installer) Configure() error {
	if i.IsInstalled() {
		return i.Upgrade()
	}
	return i.Initialize()
}

func (i *Installer) IsInstalled() bool {
	_, err := os.Stat(i.installFile)
	return err == nil
}

func (i *Installer) Initialize() error {
	if err := i.StorageChange(); err != nil {
		return err
	}
	if err := os.WriteFile(i.installFile, []byte("installed"), 0644); err != nil {
		return err
	}
	return i.UpdateVersion()
}

func (i *Installer) Upgrade() error {
	return i.UpdateVersion()
}

func (i *Installer) PreRefresh() error {
	return nil
}

func (i *Installer) PostRefresh() error {
	if err := i.UpdateConfigs(); err != nil {
		return err
	}
	if err := i.ClearVersion(); err != nil {
		return err
	}
	return i.FixPermissions()
}

func (i *Installer) AccessChange() error {
	return i.UpdateConfigs()
}

func (i *Installer) StorageChange() error {
	storageDir, err := i.platformClient.InitStorage(App, App)
	if err != nil {
		return err
	}
	return linux.Chown(storageDir, App)
}

func (i *Installer) ClearVersion() error {
	return os.RemoveAll(i.currentVersionFile)
}

func (i *Installer) UpdateVersion() error {
	return cp.Copy(i.newVersionFile, i.currentVersionFile)
}

func (i *Installer) UpdateConfigs() error {
	if err := linux.CreateUser(App); err != nil {
		return err
	}
	if err := linux.CreateMissingDirs(
		path.Join(DataDir, "config"),
		path.Join(DataDir, "nginx"),
		path.Join(DataDir, "db"),
	); err != nil {
		return err
	}
	if err := i.GenerateConfig(); err != nil {
		return fmt.Errorf("generate config: %w", err)
	}

	return i.FixPermissions()
}

func (i *Installer) GenerateConfig() error {
	token, err := i.RegistrationToken()
	if err != nil {
		return fmt.Errorf("registration token: %w", err)
	}

	appUrl, err := i.platformClient.GetAppUrl(App)
	if err != nil {
		return err
	}

	return config.Generate(
		path.Join(AppDir, "config"),
		path.Join(DataDir, "config"),
		NewVariables(appUrl, i.platformClient.GetAuthLocalSocket(), token),
	)
}

func NewVariables(url, authLocalSocket, registrationToken string) Variables {
	return Variables{
		App:               App,
		AppDir:            AppDir,
		DataDir:           DataDir,
		CommonDir:         CommonDir,
		Socket:            path.Join(DataDir, "fmd.sock"),
		Url:               url,
		AuthLocalSocket:   authLocalSocket,
		NginxSyslogTag:    NginxSyslogTag(),
		RegistrationToken: registrationToken,
	}
}

// nginx rejects a syslog tag that is not alphanumeric or underscore
func NginxSyslogTag() string {
	return strings.ReplaceAll(App, "-", "_") + "_nginx"
}

func (i *Installer) RegistrationToken() (string, error) {
	existing, err := os.ReadFile(i.tokenFile)
	if err == nil {
		token := strings.TrimSpace(string(existing))
		if token != "" {
			return token, nil
		}
	}

	buffer := make([]byte, 16)
	if _, err := rand.Read(buffer); err != nil {
		return "", err
	}
	token := hex.EncodeToString(buffer)

	if err := os.WriteFile(i.tokenFile, []byte(token+"\n"), 0640); err != nil {
		return "", err
	}
	return token, nil
}

func (i *Installer) FixPermissions() error {
	if err := linux.Chown(DataDir, App); err != nil {
		return err
	}
	return linux.Chown(CommonDir, App)
}

func (i *Installer) BackupPreStop() error    { return i.PreRefresh() }
func (i *Installer) RestorePreStart() error  { return i.PostRefresh() }
func (i *Installer) RestorePostStart() error { return i.Configure() }
