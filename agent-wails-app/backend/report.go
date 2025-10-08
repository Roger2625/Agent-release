package backend

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

type Report struct {
	ID        string                 `json:"id"`
	Title     string                 `json:"title"`
	Content   map[string]interface{} `json:"content"`
	FilePath  string                 `json:"file_path"`
	CreatedAt time.Time              `json:"created_at"`
}

type ReportGenerator struct {
	reportsDir string
	reports    []Report
}

func NewReportGenerator() *ReportGenerator {
	homeDir, _ := os.UserHomeDir()
	reportsDir := filepath.Join(homeDir, ".agent-app", "reports")

	os.MkdirAll(reportsDir, 0755)

	return &ReportGenerator{
		reportsDir: reportsDir,
		reports:    make([]Report, 0),
	}
}

func (rg *ReportGenerator) CreateReport(title string, content map[string]interface{}) (*Report, error) {
	report := &Report{
		ID:        generateID(),
		Title:     title,
		Content:   content,
		CreatedAt: time.Now(),
	}

	filename := fmt.Sprintf("report_%s_%s.json",
		time.Now().Format("20060102_150405"),
		report.ID[:8])

	report.FilePath = filepath.Join(rg.reportsDir, filename)

	jsonData, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("failed to marshal report: %w", err)
	}

	if err := os.WriteFile(report.FilePath, jsonData, 0644); err != nil {
		return nil, fmt.Errorf("failed to write report: %w", err)
	}

	rg.reports = append(rg.reports, *report)
	return report, nil
}

func (rg *ReportGenerator) ListReports() ([]Report, error) {
	files, err := os.ReadDir(rg.reportsDir)
	if err != nil {
		return nil, fmt.Errorf("failed to read reports directory: %w", err)
	}

	reports := make([]Report, 0)

	for _, file := range files {
		if file.IsDir() || filepath.Ext(file.Name()) != ".json" {
			continue
		}

		data, err := os.ReadFile(filepath.Join(rg.reportsDir, file.Name()))
		if err != nil {
			continue
		}

		var report Report
		if err := json.Unmarshal(data, &report); err != nil {
			continue
		}

		reports = append(reports, report)
	}

	return reports, nil
}

func (rg *ReportGenerator) GetReport(id string) (*Report, error) {
	reports, err := rg.ListReports()
	if err != nil {
		return nil, err
	}

	for _, report := range reports {
		if report.ID == id {
			return &report, nil
		}
	}

	return nil, fmt.Errorf("report not found")
}

func (rg *ReportGenerator) DeleteReport(id string) error {
	report, err := rg.GetReport(id)
	if err != nil {
		return err
	}

	return os.Remove(report.FilePath)
}

func generateID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}
