# Code Review Checklist

## Before Creating a Pull Request

### Code Quality
- [ ] Code follows project style guide
- [ ] No console.log or debug statements
- [ ] Proper error handling
- [ ] No hardcoded credentials
- [ ] Functions have single responsibility

### Testing
- [ ] Unit tests added/updated
- [ ] All tests passing
- [ ] Edge cases covered
- [ ] Integration tests (if needed)

### Documentation
- [ ] README updated (if needed)
- [ ] API documentation updated
- [ ] Inline comments for complex logic
- [ ] Changelog updated

### Security
- [ ] No SQL injection risks
- [ ] No XSS vulnerabilities
- [ ] Input validation present
- [ ] Authentication/authorization checks

### Performance
- [ ] No obvious performance issues
- [ ] Database queries optimized
- [ ] No unnecessary re-renders (frontend)
- [ ] Resource cleanup implemented
