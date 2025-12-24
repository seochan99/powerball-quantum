#!/usr/bin/env node

import { Command } from 'commander';
import { predict, updateData, formatPick } from './index';

const program = new Command();

program
  .name('powerball-quantum')
  .description('Powerball number predictor using quantum-inspired algorithm')
  .version('1.0.0');

program
  .command('predict')
  .description('Generate predicted Powerball numbers')
  .option('-c, --count <number>', 'Number of picks to generate', '5')
  .option('-a, --analysis', 'Show signal analysis', false)
  .action(async (options) => {
    console.log('');
    console.log('🎱 POWERBALL QUANTUM PREDICTOR');
    console.log('═'.repeat(50));

    try {
      const picks = await predict({
        count: parseInt(options.count),
        showAnalysis: options.analysis
      });

      console.log('\n⭐ RECOMMENDED PICKS:\n');

      picks.forEach((pick, i) => {
        const score = pick.score?.toFixed(1) || '?';
        console.log(`  #${i + 1}  ${formatPick(pick)}  (score: ${score})`);
      });

      console.log('\n' + '═'.repeat(50));
      console.log('Good luck! 🍀\n');
    } catch (error) {
      console.error('Error:', error);
      process.exit(1);
    }
  });

program
  .command('update')
  .description('Update Powerball data from NY Lottery API')
  .action(async () => {
    console.log('');
    console.log('📥 Updating Powerball data...');
    console.log('═'.repeat(50));

    try {
      await updateData();
      console.log('✅ Data updated successfully!\n');
    } catch (error) {
      console.error('Error updating data:', error);
      process.exit(1);
    }
  });

program
  .command('quick')
  .description('Get one quick pick')
  .action(async () => {
    try {
      const picks = await predict({ count: 1 });
      if (picks[0]) {
        console.log('\n🎫 Your lucky numbers:');
        console.log(`\n   ${formatPick(picks[0])}\n`);
      }
    } catch (error) {
      console.error('Error:', error);
      process.exit(1);
    }
  });

// Default action (no command)
if (process.argv.length === 2) {
  program.parse(['node', 'cli', 'predict']);
} else {
  program.parse();
}
