export enum SENDER {
  USER = "user",
  BOT = "bot",
}

export type Message = {
  sender: SENDER;
  content: string;
  timestamp: Date;
  attachment?: string;
};

export type LatestJobs = {
  jobs: Jobs[];
  jobs_found: boolean;
};

export type Jobs = {
  id: string;
  job_title: string;
  location: Array<string>;
  min_experience: number;
};
