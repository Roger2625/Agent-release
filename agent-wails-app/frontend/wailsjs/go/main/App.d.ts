export function ValidateAPIKey(arg1: string, arg2: string): Promise<{ [key: string]: any }>;

export function GetData(arg1: string, arg2: string, arg3: { [key: string]: any }): Promise<{ [key: string]: any }>;

export function SaveConfiguration(arg1: string, arg2: string): Promise<void>;

export function LoadConfiguration(): Promise<{ [key: string]: any }>;

export function ExecuteCommand(arg1: string): Promise<string>;

export function GetSessionHistory(): Promise<Array<{ [key: string]: any }>>;

export function CreateReport(arg1: string, arg2: { [key: string]: any }): Promise<{ [key: string]: any }>;

export function ListReports(): Promise<Array<{ [key: string]: any }>>;

export function GetReport(arg1: string): Promise<{ [key: string]: any }>;

export function DeleteReport(arg1: string): Promise<void>;
