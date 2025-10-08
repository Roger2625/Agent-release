package backend

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

type Config struct {
	ServerURL string `json:"server_url"`
	Token     string `json:"token"`
	configDir string
	configFile string
}

func NewConfig() *Config {
	homeDir, _ := os.UserHomeDir()
	configDir := filepath.Join(homeDir, ".agent-app")

	return &Config{
		configDir:  configDir,
		configFile: filepath.Join(configDir, "client.conf.json"),
	}
}

func (c *Config) Save(serverURL, token string) error {
	if err := os.MkdirAll(c.configDir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	c.ServerURL = serverURL
	c.Token = token

	data := map[string]string{
		"server_url": serverURL,
		"token":      token,
	}

	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(c.configFile, jsonData, 0600); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

func (c *Config) Load() (map[string]interface{}, error) {
	if _, err := os.Stat(c.configFile); os.IsNotExist(err) {
		return nil, nil
	}

	data, err := os.ReadFile(c.configFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var config map[string]interface{}
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}

	if serverURL, ok := config["server_url"].(string); ok {
		c.ServerURL = serverURL
	}
	if token, ok := config["token"].(string); ok {
		c.Token = token
	}

	return config, nil
}

func (c *Config) Exists() bool {
	_, err := os.Stat(c.configFile)
	return err == nil
}
