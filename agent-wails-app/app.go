package main

import (
	"context"
	"agent-app/backend"
)

type App struct {
	ctx       context.Context
	api       *backend.API
	config    *backend.Config
	session   *backend.Session
	reportGen *backend.ReportGenerator
}

func NewApp() *App {
	return &App{
		api:       backend.NewAPI(),
		config:    backend.NewConfig(),
		session:   backend.NewSession(),
		reportGen: backend.NewReportGenerator(),
	}
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	a.config.Load()
}

func (a *App) ValidateAPIKey(serverURL, apiKey string) (map[string]interface{}, error) {
	return a.api.ValidateAPIKey(serverURL, apiKey)
}

func (a *App) GetData(serverURL, token string, params map[string]interface{}) (map[string]interface{}, error) {
	return a.api.GetData(serverURL, token, params)
}

func (a *App) SaveConfiguration(serverURL, token string) error {
	return a.config.Save(serverURL, token)
}

func (a *App) LoadConfiguration() (map[string]interface{}, error) {
	return a.config.Load()
}

func (a *App) ExecuteCommand(command string) (string, error) {
	return a.session.ExecuteCommand(command)
}

func (a *App) GetSessionHistory() []map[string]interface{} {
	return a.session.GetHistory()
}

func (a *App) CreateReport(title string, content map[string]interface{}) (map[string]interface{}, error) {
	report, err := a.reportGen.CreateReport(title, content)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"id":         report.ID,
		"title":      report.Title,
		"content":    report.Content,
		"file_path":  report.FilePath,
		"created_at": report.CreatedAt.Format("2006-01-02 15:04:05"),
	}, nil
}

func (a *App) ListReports() ([]map[string]interface{}, error) {
	reports, err := a.reportGen.ListReports()
	if err != nil {
		return nil, err
	}

	result := make([]map[string]interface{}, len(reports))
	for i, report := range reports {
		result[i] = map[string]interface{}{
			"id":         report.ID,
			"title":      report.Title,
			"content":    report.Content,
			"file_path":  report.FilePath,
			"created_at": report.CreatedAt.Format("2006-01-02 15:04:05"),
		}
	}

	return result, nil
}

func (a *App) GetReport(id string) (map[string]interface{}, error) {
	report, err := a.reportGen.GetReport(id)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"id":         report.ID,
		"title":      report.Title,
		"content":    report.Content,
		"file_path":  report.FilePath,
		"created_at": report.CreatedAt.Format("2006-01-02 15:04:05"),
	}, nil
}

func (a *App) DeleteReport(id string) error {
	return a.reportGen.DeleteReport(id)
}
