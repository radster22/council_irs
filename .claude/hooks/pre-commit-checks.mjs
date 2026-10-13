import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

const projectRoot = process.env.CLAUDE_PROJECT_DIR ?? process.cwd();

function run(command, args, cwd = projectRoot) {
  const result = spawnSync(command, args, {
    cwd,
    stdio: 'inherit',
    shell: process.platform === 'win32',
  });

  if (result.error) {
    console.error(`Could not start ${command}: ${result.error.message}`);
    process.exit(1);
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

if (!existsSync(resolve(projectRoot, '.gitignore'))) {
  console.error(`Project root not found: ${projectRoot}`);
  process.exit(1);
}

if (existsSync(resolve(projectRoot, 'backend'))) {
  run('python', ['-m', 'compileall', '-q', 'backend/app']);
  run('python', ['-m', 'pytest', 'backend/tests', '-q']);
}

const frontendDir = resolve(projectRoot, 'frontend');
if (existsSync(resolve(frontendDir, 'package.json'))) {
  run('npm', ['run', 'lint'], frontendDir);
  run('npm', ['test', '--', '--run'], frontendDir);
  run('npm', ['run', 'build'], frontendDir);
}

run('git', ['diff', '--check']);
run('git', ['diff', '--cached', '--check']);
