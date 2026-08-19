export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type TaskReport = {
  title: string;
  summary: string;
  category: string;
  suggestedReward: string;
  deadline: string;
  deliverables: string[];
  objectiveCriteria: { field: string; rule: string }[];
  subjectiveCriteria: { description: string; weight: number }[];
  acceptanceNotes: string;
};

export type ClarifyResponse = {
  reply: string;
  readyForReport: boolean;
};

export type ReportResponse = {
  report: TaskReport;
};
