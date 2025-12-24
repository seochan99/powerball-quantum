export interface Draw {
  date: Date;
  whiteBalls: number[];
  powerball: number;
  multiplier: number;
}

export interface Pick {
  whiteBalls: number[];
  powerball: number;
  score?: number;
}

export interface Scores {
  [key: number]: number;
}

export interface PredictOptions {
  count?: number;
  showAnalysis?: boolean;
}

export const WHITE_BALL_RANGE = { min: 1, max: 69 };
export const RED_BALL_RANGE = { min: 1, max: 26 };
export const DATA_URL = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD";
