import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { Draw, DATA_URL } from './types';

const DATA_FILE = path.join(__dirname, '..', 'powerball_data.csv');

/**
 * Download latest Powerball data from NY Lottery API
 */
export async function downloadData(): Promise<string> {
  console.log('Downloading latest Powerball data...');
  const response = await axios.get(DATA_URL);
  fs.writeFileSync(DATA_FILE, response.data);
  console.log('Download complete!');
  return DATA_FILE;
}

/**
 * Parse CSV data into Draw objects
 */
export function parseCSV(csvContent: string): Draw[] {
  const lines = csvContent.trim().split('\n');
  const draws: Draw[] = [];

  // Skip header
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const parts = line.split(',');
    if (parts.length < 3) continue;

    const dateStr = parts[0];
    const numbersStr = parts[1];
    const multiplier = parseInt(parts[2]) || 2;

    const numbers = numbersStr.split(' ').map(n => parseInt(n.trim()));
    if (numbers.length < 6) continue;

    const date = new Date(dateStr);
    // Filter for current rules (post Oct 7, 2015)
    if (date < new Date('2015-10-07')) continue;

    draws.push({
      date,
      whiteBalls: numbers.slice(0, 5),
      powerball: numbers[5],
      multiplier
    });
  }

  return draws;
}

/**
 * Load data from file or download if not exists
 */
export async function loadData(): Promise<Draw[]> {
  let csvContent: string;

  if (fs.existsSync(DATA_FILE)) {
    csvContent = fs.readFileSync(DATA_FILE, 'utf-8');
  } else {
    await downloadData();
    csvContent = fs.readFileSync(DATA_FILE, 'utf-8');
  }

  const draws = parseCSV(csvContent);
  console.log(`Loaded ${draws.length} draws (current rules since 2015-10-07)`);
  return draws;
}

/**
 * Update data (force re-download)
 */
export async function updateData(): Promise<Draw[]> {
  await downloadData();
  const csvContent = fs.readFileSync(DATA_FILE, 'utf-8');
  const draws = parseCSV(csvContent);
  console.log(`Updated! ${draws.length} draws loaded.`);
  return draws;
}
