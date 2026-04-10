# Contributing to Alpha Skills

Thanks for your interest! Here's how you can help.

## Adding a New Skill

1. Create `skills/your-skill-name/SKILL.md`
2. Follow the existing skill format (see any `skills/alpha-*/SKILL.md` for reference)
3. Requirements:
   - YAML frontmatter with `name` and `description` (bilingual EN/ZH)
   - Trigger phrases in both English and Chinese
   - Self-contained Python code (no external package imports)
   - Bilingual output format (table headers in both languages)
4. Test your skill end-to-end
5. Submit a PR

## Adding a Data Adapter

1. Create `examples/your_data_source.py`
2. Implement the 7 required functions (see `examples/README.md`)
3. Include a `MARKET_CONFIG` dict
4. Add cache support for API-based sources
5. Submit a PR

## Improving Existing Skills

- Fix bugs or edge cases
- Add new factor implementations to the inline code
- Improve evaluation methodology
- Better output formatting
- Translation improvements

## Code Style

- Python code in skills should be self-contained and readable
- Use type hints in function signatures
- Include bilingual comments for key logic

## Questions?

Open an issue on GitHub.
