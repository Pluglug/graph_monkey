# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MonKey (Graph Monkey)

Blender animation addon for Graph Editor workflow enhancement. Version 0.9.0, Blender 2.80+.

**Features**: Keyframe manipulation, playback controls, pose visualization.

## Quick Reference

| Task | Rule File |
|------|-----------|
| Understanding the addon | `.claude/rules/01-overview.md` |
| Module loading system | `.claude/rules/02-architecture.md` |
| Adding operators | `.claude/rules/03-adding-operators.md` |
| Adding settings | `.claude/rules/04-adding-settings.md` |
| Keymap registration | `.claude/rules/05-keymap-system.md` |
| Utility modules | `.claude/rules/06-utilities.md` |
| Coding conventions | `.claude/rules/07-conventions.md` |
| New feature guidelines | `.claude/rules/08-new-feature-guidelines.md` |

## Essential Points

- **Auto-registration**: No manual `register_class()` needed - place files in correct directory
- **pyright directive**: Files with PropertyGroup need `# pyright: reportInvalidTypeForm=false` at top
- **Language**: Japanese and English comments both acceptable
