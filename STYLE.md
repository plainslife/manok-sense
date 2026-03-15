# Code Style Guide
 
## Naming
- Use `_prefix` for internal properties and methods e.g. `self._device`
- Use `snake_case` for all variables, functions, and files e.g. `generate_filename()`
- Use `PascalCase` for class names e.g. `DisplayUI`, `TouchInput`
- Use `UPPER_SNAKE_CASE` for constants e.g. `BTN_RADIUS`, `DISPLAY_WIDTH`
 
## Encapsulation
- Expose public methods instead of accessing internals directly
- e.g. use `display.push(canvas)` not `display._device.display(canvas)`
 
## Commits (optional)
- `feat:` new feature, `fix:` bug fix, `refactor:` restructure, `chore:` config/setup

## Git Workflow
- Create a new branch for each feature or fix e.g. `feat/animation` or `fix/touch-import`
- Never commit directly to `main`
- Push your branch and open a pull request for teammates to review 
