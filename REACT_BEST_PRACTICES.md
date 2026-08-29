# React Best Practices Guide

## Component Structure

### Functional Components Only
- Use function components with hooks (no class components)
- Export named function before default export for easier debugging
- Keep components focused on a single responsibility

```javascript
// Good
export function UserCard({ user }) {
  return <div>{user.name}</div>;
}

export default UserCard;
```

### File Organization
- One component per file (unless very tightly coupled)
- Co-locate styles, tests, and hooks with their components
- Use index.js for directory exports

```
components/
  UserCard/
    index.js
    UserCard.jsx
    UserCard.module.css
    useUserCard.js
    UserCard.test.js
```

## Hooks & State Management

### Hook Rules (ESLint)
- Call hooks at the top level only (not in loops, conditions)
- Call hooks only from React functions
- Use custom hooks to share stateful logic

### State Management Best Practices
- Keep state as close to where it's used as possible
- Use `useState` for component-level state
- Use `useReducer` for complex state transitions
- Use context only for truly global state (theme, auth)
- Prefer props drilling over context for local state

```javascript
// Good - state near usage
function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

### useEffect Best Practices
- Include proper dependency arrays
- Clean up subscriptions/timers in return
- Separate concerns into multiple useEffect calls
- Avoid recreating objects/functions in dependency arrays

```javascript
// Good
useEffect(() => {
  const timer = setTimeout(() => {
    setData(value);
  }, 1000);
  
  return () => clearTimeout(timer);
}, [value]);
```

## Performance Optimization

### Memoization Strategy
- Use `React.memo()` for expensive components that receive same props
- Use `useMemo()` for expensive computations
- Use `useCallback()` to memoize callback functions passed to memo'd children
- Only optimize after profiling shows a real problem

```javascript
// Good - memoize expensive child
const UserList = React.memo(({ users, onSelect }) => {
  return users.map(u => <UserItem key={u.id} user={u} onClick={onSelect} />);
});
```

### Rendering Optimization
- Use keys with stable IDs (database IDs, not array indices)
- Avoid inline object/array literals in props
- Split components to reduce re-render scope

```javascript
// Bad - new object every render
<Component style={{ color: 'red' }} />

// Good - stable reference
const buttonStyle = { color: 'red' };
<Component style={buttonStyle} />
```

## Code Quality

### Naming Conventions
- Components: PascalCase
- Functions/variables: camelCase
- Constants: UPPER_SNAKE_CASE (only for true constants)
- Event handlers: onEventName
- Custom hooks: useHookName

### Conditional Rendering
- Use ternary for simple conditions
- Use logical && only when no fallback needed
- Extract complex conditionals to separate functions

```javascript
// Good
function Status({ user }) {
  if (user.isLoading) return <Spinner />;
  if (user.error) return <Error message={user.error} />;
  return <UserInfo user={user} />;
}
```

### Props Validation
- Destructure props at function signature when possible
- Document props with TypeScript or JSDoc
- Use default values for optional props

```javascript
// Good with TypeScript
interface UserCardProps {
  user: User;
  onClick?: (id: string) => void;
}

function UserCard({ user, onClick }: UserCardProps) {
  // ...
}
```

## Form Handling

- Use controlled components for forms (value + onChange)
- Create reusable form components (Input, Select, Checkbox)
- Use a form library for complex forms (React Hook Form, Formik)
- Validate on change and blur, show errors on blur

```javascript
// Good
function LoginForm() {
  const [email, setEmail] = useState('');
  
  return (
    <input 
      type="email" 
      value={email} 
      onChange={(e) => setEmail(e.target.value)}
    />
  );
}
```

## Testing

- Test behavior, not implementation
- Use React Testing Library (not Enzyme)
- Test accessibility alongside functionality
- Mock external dependencies, not internal components

```javascript
// Good
test('shows error when email is invalid', () => {
  render(<LoginForm />);
  const input = screen.getByRole('textbox', { name: /email/i });
  fireEvent.change(input, { target: { value: 'invalid' } });
  expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
});
```

## Styling

### CSS Organization
- Use CSS Modules for component-scoped styles
- Use BEM or similar naming for global styles
- Keep responsive breakpoints consistent
- Use CSS variables for theming

```css
/* UserCard.module.css */
.card {
  padding: 1rem;
  border-radius: 8px;
}

.cardTitle {
  font-size: 1.5rem;
  font-weight: 600;
}
```

### Utility-First (Tailwind) Alternative
- Use Tailwind for rapid development
- Extract common patterns into components
- Don't over-abstract utilities into classes

```javascript
// Good - semantic component
function Button({ children }) {
  return (
    <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
      {children}
    </button>
  );
}
```

## Error Handling

- Create Error Boundary components for critical sections
- Handle async errors in useEffect
- Provide user-friendly error messages
- Log errors for debugging (production monitoring)

```javascript
// Good Error Boundary
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    console.error(error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

## Async Operations

- Use `useEffect` with cleanup for side effects
- Use async/await over .then() chains
- Handle loading and error states explicitly
- Prevent state updates on unmounted components

```javascript
// Good
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    let isMounted = true;
    
    async function fetchUser() {
      setLoading(true);
      const data = await api.getUser(userId);
      if (isMounted) setUser(data);
      setLoading(false);
    }
    
    fetchUser();
    return () => { isMounted = false; };
  }, [userId]);
}
```

## Accessibility (a11y)

- Use semantic HTML (button, form, nav, etc.)
- Include alt text for images
- Ensure keyboard navigation works
- Use ARIA labels when needed
- Test with screen readers

```javascript
// Good
<button aria-label="Close dialog" onClick={onClose}>✕</button>
<img src="user.jpg" alt="Profile picture of John" />
```

## Common Anti-Patterns to Avoid

❌ Creating components inside render
- Causes unnecessary remounting and state loss

❌ Using array index as key
- Causes bugs when list reorders

❌ Mutating state directly
- Use setState/hooks instead

❌ Putting too much logic in JSX
- Extract to functions or custom hooks

❌ Ignoring useEffect dependency array
- Causes infinite loops or stale closures

❌ Creating objects/functions in render
- Use useMemo/useCallback or move outside

## Git Copilot Instruction Template

When using this with Copilot, save as `.github/copilot-instructions.md` in your repo:

```markdown
# Copilot Instructions for React Code

Follow these practices when generating React code:

1. Use functional components with hooks (no classes)
2. Keep components single-responsibility
3. Use proper dependency arrays in useEffect
4. Write controlled forms with onChange handlers
5. Include proper error handling and loading states
6. Use TypeScript for props when available
7. Write accessible HTML with semantic elements
8. Test behavior, not implementation
9. Use React Testing Library for tests
10. Prefer composition over deep component nesting
```

## Quick Reference Checklist

- [ ] Component has single responsibility
- [ ] All hooks have correct dependency arrays
- [ ] Props are documented (TS or JSDoc)
- [ ] Form inputs are controlled components
- [ ] Loading and error states handled
- [ ] No array indices used as keys
- [ ] Semantic HTML used
- [ ] Component is testable
- [ ] Performance optimized after profiling
- [ ] Error boundaries in place for critical sections
