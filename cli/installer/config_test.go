package installer

import (
	"os"
	"path"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/syncloud/golib/config"
)

const token = "0123456789abcdef0123456789abcdef"

func generate(t *testing.T) string {
	output := t.TempDir()

	variables := NewVariables(
		"https://fmd-server.example.com",
		"http://unix:/var/snap/platform/current/authelia.socket:",
		token,
	)

	require.NoError(t, config.Generate("../../config", output, variables))
	return output
}

func read(t *testing.T, dir, name string) string {
	content, err := os.ReadFile(path.Join(dir, name))
	require.NoError(t, err)
	return string(content)
}

func TestConfigTemplatesRender(t *testing.T) {
	output := generate(t)

	entries, err := os.ReadDir(output)
	require.NoError(t, err)
	require.Len(t, entries, 5)

	for _, entry := range entries {
		assert.NotContains(t, read(t, output, entry.Name()), "{{", entry.Name())
	}
}

func TestServerConfigDisablesTcpPorts(t *testing.T) {
	content := read(t, generate(t), "fmd-server.yml")

	assert.Contains(t, content, `PortSecure: ""`)
	assert.Contains(t, content, `PortInsecure: ""`)
	assert.Contains(t, content, `MetricsAddrPort: ""`)
}

func TestTokenPageShowsTokenAndUrl(t *testing.T) {
	content := read(t, generate(t), "syncloud.html")

	assert.Contains(t, content, token)
	assert.Contains(t, content, "https://fmd-server.example.com")
}

func TestOnlyTheTokenPageIsBehindAuth(t *testing.T) {
	content := read(t, generate(t), "nginx.conf")

	page := strings.Index(content, "location = /syncloud")
	app := strings.Index(content, "location / ")
	require.Positive(t, page)
	require.Greater(t, app, page)

	assert.Contains(t, content[page:app], "authelia-authrequest.conf",
		"the token page is a secret, it must require a syncloud login")
	assert.NotContains(t, content[app:], "authelia-authrequest.conf",
		"fmd authenticates its own clients, the app itself must not be gated")
}

func TestTokenPageIsLinkedFromTheApp(t *testing.T) {
	content := read(t, generate(t), "nginx.conf")

	assert.Contains(t, content, "sub_filter '</body>'")
	assert.Contains(t, content, `href="/syncloud"`)
	assert.Contains(t, content, `proxy_set_header Accept-Encoding ""`,
		"sub_filter cannot rewrite a compressed response")
}

func TestTokenIsNotInTheAppConfigs(t *testing.T) {
	output := generate(t)

	assert.NotContains(t, read(t, output, "nginx.conf"), token)
	assert.Contains(t, read(t, output, "fmd-server.yml"), token)
}

func TestNginxSyslogTagIsLegal(t *testing.T) {
	tag := NginxSyslogTag()

	assert.Contains(t, tag, "fmd")
	assert.Regexp(t, `^[a-z0-9_]{1,32}$`, tag,
		"nginx refuses to start with a tag that is not alphanumeric or underscore")
	assert.Contains(t, read(t, generate(t), "nginx.conf"), "tag="+tag)
}
