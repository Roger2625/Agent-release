package backend

import (
	"bytes"
	"fmt"
	"os/exec"
	"time"
)

type CommandHistory struct {
	Command   string    `json:"command"`
	Output    string    `json:"output"`
	Timestamp time.Time `json:"timestamp"`
	Success   bool      `json:"success"`
}

type Session struct {
	history []CommandHistory
}

func NewSession() *Session {
	return &Session{
		history: make([]CommandHistory, 0),
	}
}

func (s *Session) ExecuteCommand(command string) (string, error) {
	cmd := exec.Command("sh", "-c", command)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()

	output := stdout.String()
	if stderr.Len() > 0 {
		output += "\n" + stderr.String()
	}

	history := CommandHistory{
		Command:   command,
		Output:    output,
		Timestamp: time.Now(),
		Success:   err == nil,
	}

	s.history = append(s.history, history)

	if err != nil {
		return output, fmt.Errorf("command failed: %w", err)
	}

	return output, nil
}

func (s *Session) GetHistory() []map[string]interface{} {
	result := make([]map[string]interface{}, len(s.history))

	for i, h := range s.history {
		result[i] = map[string]interface{}{
			"command":   h.Command,
			"output":    h.Output,
			"timestamp": h.Timestamp.Format(time.RFC3339),
			"success":   h.Success,
		}
	}

	return result
}

func (s *Session) ClearHistory() {
	s.history = make([]CommandHistory, 0)
}
