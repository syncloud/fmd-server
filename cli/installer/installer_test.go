package installer

import (
	"os"
	"path"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func tempInstaller(t *testing.T) *Installer {
	return &Installer{tokenFile: path.Join(t.TempDir(), "registration.token")}
}

func TestRegistrationTokenIsGenerated(t *testing.T) {
	token, err := tempInstaller(t).RegistrationToken()

	require.NoError(t, err)
	assert.Len(t, token, 32)
}

func TestRegistrationTokenIsStable(t *testing.T) {
	i := tempInstaller(t)

	first, err := i.RegistrationToken()
	require.NoError(t, err)
	second, err := i.RegistrationToken()
	require.NoError(t, err)

	assert.Equal(t, first, second)
}

func TestRegistrationTokenReplacesEmptyFile(t *testing.T) {
	i := tempInstaller(t)
	require.NoError(t, os.WriteFile(i.tokenFile, []byte("\n"), 0640))

	token, err := i.RegistrationToken()

	require.NoError(t, err)
	assert.NotEmpty(t, token)
}
