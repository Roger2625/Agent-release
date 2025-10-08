// @ts-check

export function ValidateAPIKey(arg1, arg2) {
  return window['go']['main']['App']['ValidateAPIKey'](arg1, arg2);
}

export function GetData(arg1, arg2, arg3) {
  return window['go']['main']['App']['GetData'](arg1, arg2, arg3);
}

export function SaveConfiguration(arg1, arg2) {
  return window['go']['main']['App']['SaveConfiguration'](arg1, arg2);
}

export function LoadConfiguration() {
  return window['go']['main']['App']['LoadConfiguration']();
}

export function ExecuteCommand(arg1) {
  return window['go']['main']['App']['ExecuteCommand'](arg1);
}

export function GetSessionHistory() {
  return window['go']['main']['App']['GetSessionHistory']();
}

export function CreateReport(arg1, arg2) {
  return window['go']['main']['App']['CreateReport'](arg1, arg2);
}

export function ListReports() {
  return window['go']['main']['App']['ListReports']();
}

export function GetReport(arg1) {
  return window['go']['main']['App']['GetReport'](arg1);
}

export function DeleteReport(arg1) {
  return window['go']['main']['App']['DeleteReport'](arg1);
}
