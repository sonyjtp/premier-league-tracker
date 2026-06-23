import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      // New react-hooks v7 rules — valid patterns used throughout this codebase,
      // downgraded to warn until components are refactored to React Compiler conventions.
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/purity': 'warn',

      // API responses are untyped; warn until proper response schemas are added.
      '@typescript-eslint/no-explicit-any': 'warn',

      // Context files legitimately export hooks and constants alongside components.
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],

      // Allow _-prefixed identifiers as intentionally unused (e.g. destructured props).
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      }],
    },
  },
])
