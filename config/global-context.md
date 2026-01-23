# Global Project Context v2.2

> **MISSION:** Build production-ready code that works correctly the first time.

---

## ⚡ QUICK REFERENCE (Read This First!)

### ✅ ALWAYS DO:

**Security:**
- SQL: `$stmt->execute([$id])` — NEVER string concatenation
- Output: `htmlspecialchars($x, ENT_QUOTES, 'UTF-8')` — escape ALL user input
- Passwords: `password_hash($p, PASSWORD_BCRYPT)` — NEVER plain text or MD5
- Forms: Include `<input type="hidden" name="csrf_token">` on every POST form
- Sessions: `session_regenerate_id(true)` after login
- Protected pages: `require 'auth_check.php';` at the TOP of every protected file

**Database:**
- Charset: `utf8mb4` with `utf8mb4_0900_ai_ci` collation (MySQL 8.0+ default)
- Indexes: Add `INDEX` on columns used in WHERE/JOIN
- Transactions: Use `beginTransaction/commit/rollBack` for related operations

**UI:**
- Links: Relative paths `href="about.php"` — NOT `/about.php`
- Grid: Always include `grid-cols-*` (e.g., `grid grid-cols-1 md:grid-cols-3`)
- Flex: Always include direction `flex-row` or `flex-col`
- Dark backgrounds: Use light text `bg-gray-800 text-white`

**Design (Tailwind):**
- Spacing: Use 4px grid (`gap-2`=8px, `gap-4`=16px, `gap-6`=24px)
- Colors: 60% neutral (`gray-50`), 30% secondary (`gray-100-200`), 10% accent (`blue-600`)
- No pure black/white: Use `gray-900` and `gray-50` instead
- Buttons: `px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md`
- Cards: `bg-white rounded-lg shadow-sm border border-gray-200 p-6`
- Inputs: `w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500`
- Dark mode: Always add `dark:` variants (`dark:bg-gray-800 dark:text-white`)

### ❌ NEVER DO:

| Bad | Why | Good |
|-----|-----|------|
| `"WHERE id=$id"` | SQL Injection | `"WHERE id=?"` + bind |
| `echo $userInput` | XSS Attack | `echo htmlspecialchars($userInput)` |
| `$password` in code | Credential leak | `$_ENV['DB_PASS']` from .env |
| `href="/page.php"` | Breaks in subfolders | `href="page.php"` |
| `grid gap-4` | No columns defined | `grid grid-cols-3 gap-4` |
| `flex gap-4` | No direction | `flex flex-row gap-4` |

### 🧪 TEST COMMANDS:

```bash
# PHP Tests
php tests/MyTest.php

# Python Tests
pytest -v tests/

# UI Verification (screenshots + console errors)
python /opt/codehero/scripts/verify_ui.py https://127.0.0.1:9867/myproject/

# Check server logs
sudo tail -20 /var/log/nginx/codehero-projects-error.log
```

### 📁 WORKSPACE:

```
Web projects:  /var/www/projects/{name}/
App projects:  /opt/apps/{name}/

FORBIDDEN:     /opt/codehero/, /etc/nginx/, /etc/systemd/
```

---

## PART 1: SECURITY (NON-NEGOTIABLE)

### 1.1 FORBIDDEN PATHS

```
NEVER TOUCH:
/opt/codehero/          - Platform code
/etc/codehero/          - Platform config
/etc/nginx/             - Web server
/etc/systemd/           - System services

YOUR WORKSPACE:
/var/www/projects/{project}/   - Web projects
/opt/apps/{project}/           - App projects
```

### 1.2 SQL INJECTION PREVENTION

**NEVER concatenate user input into SQL. ALWAYS use prepared statements.**

```php
// PHP - PDO
$stmt = $pdo->prepare("SELECT * FROM users WHERE email = ? AND status = ?");
$stmt->execute([$email, $status]);
$user = $stmt->fetch();

// PHP - MySQLi
$stmt = $mysqli->prepare("SELECT * FROM users WHERE id = ?");
$stmt->bind_param("i", $id);
$stmt->execute();
```

```python
# Python
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
user = cursor.fetchone()
```

```java
// Java - JDBC
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE email = ?");
stmt.setString(1, email);
ResultSet rs = stmt.executeQuery();

// Java - JPA
@Query("SELECT u FROM User u WHERE u.email = :email")
Optional<User> findByEmail(@Param("email") String email);
```

```javascript
// Node.js - MySQL2
const [rows] = await pool.execute('SELECT * FROM users WHERE email = ?', [email]);
```

### 1.3 XSS PREVENTION

**ALWAYS escape output. NEVER trust user input.**

```php
// PHP - HTML output
echo htmlspecialchars($userInput, ENT_QUOTES, 'UTF-8');

// PHP - In attributes
<input value="<?= htmlspecialchars($value, ENT_QUOTES, 'UTF-8') ?>">

// PHP - JSON output
header('Content-Type: application/json');
echo json_encode($data, JSON_HEX_TAG | JSON_HEX_AMP);
```

```javascript
// JavaScript - DOM
element.textContent = userInput;  // Safe
element.innerHTML = userInput;    // DANGEROUS!

// With sanitization
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

### 1.4 PASSWORD SECURITY

```php
// PHP - Hashing
$hash = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);

// PHP - Verification
if (password_verify($inputPassword, $storedHash)) {
    // Password correct
}
```

```python
# Python
import bcrypt
hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
if bcrypt.checkpw(input_password.encode(), stored_hash):
    # Password correct
```

```java
// Java
BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(12);
String hash = encoder.encode(password);
if (encoder.matches(inputPassword, storedHash)) {
    // Password correct
}
```

### 1.5 CSRF PROTECTION

```php
// PHP - Generate token (on session start)
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

// PHP - In every form
<form method="POST">
    <input type="hidden" name="csrf_token" value="<?= $_SESSION['csrf_token'] ?>">
    <!-- form fields -->
</form>

// PHP - Validate on every POST
function validateCsrf() {
    if (!isset($_POST['csrf_token']) ||
        !hash_equals($_SESSION['csrf_token'], $_POST['csrf_token'])) {
        http_response_code(403);
        die('CSRF validation failed');
    }
}
```

```java
// Spring - Auto-configured, just enable
@Configuration
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.csrf(csrf -> csrf.csrfTokenRepository(
            CookieCsrfTokenRepository.withHttpOnlyFalse()
        ));
        return http.build();
    }
}
```

### 1.6 SESSION SECURITY

```php
// PHP - php.ini or runtime
ini_set('session.cookie_httponly', 1);    // No JS access
ini_set('session.cookie_secure', 1);       // HTTPS only
ini_set('session.cookie_samesite', 'Strict');
ini_set('session.use_strict_mode', 1);

// Regenerate session ID after login
session_regenerate_id(true);
```

```java
// Spring - application.properties
server.servlet.session.cookie.http-only=true
server.servlet.session.cookie.secure=true
server.servlet.session.cookie.same-site=strict
server.servlet.session.timeout=30m
```

### 1.7 RATE LIMITING

```php
// PHP - Simple implementation with APCu
function checkRateLimit($key, $maxAttempts, $windowSeconds) {
    $attempts = apcu_fetch($key) ?: 0;
    if ($attempts >= $maxAttempts) {
        http_response_code(429);
        die(json_encode(['error' => 'Too many attempts. Try again later.']));
    }
    apcu_store($key, $attempts + 1, $windowSeconds);
}

// Usage
checkRateLimit('login_' . $_SERVER['REMOTE_ADDR'], 5, 900);  // 5 attempts per 15 min
checkRateLimit('api_' . $userId, 100, 60);                     // 100 requests per minute
```

### 1.8 FILE UPLOAD SECURITY

```php
function handleSecureUpload($file, $uploadDir = '/var/www/uploads/') {
    // Whitelist allowed extensions
    $allowed = ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx'];
    $maxSize = 10 * 1024 * 1024; // 10MB

    // Validate
    if ($file['error'] !== UPLOAD_ERR_OK) {
        throw new Exception('Upload failed');
    }
    if ($file['size'] > $maxSize) {
        throw new Exception('File too large');
    }

    $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
    if (!in_array($ext, $allowed)) {
        throw new Exception('File type not allowed');
    }

    // Generate safe filename (NEVER use original filename in path)
    $newName = bin2hex(random_bytes(16)) . '.' . $ext;
    $destination = $uploadDir . $newName;

    // Move file
    if (!move_uploaded_file($file['tmp_name'], $destination)) {
        throw new Exception('Failed to save file');
    }

    return $newName;
}
```

### 1.9 CREDENTIALS

**NEVER hardcode credentials. ALWAYS use environment variables.**

```
# .env file (NEVER commit to git)
DB_HOST=localhost
DB_NAME=myapp
DB_USER=myuser
DB_PASS=secretpassword
API_KEY=sk_live_xxxxx
```

```php
// PHP - Load with vlucas/phpdotenv
$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();

$dbHost = $_ENV['DB_HOST'] ?? 'localhost';
$apiKey = $_ENV['API_KEY'] ?? throw new Exception('API_KEY required');
```

```python
# Python
from dotenv import load_dotenv
import os

load_dotenv()
db_host = os.getenv('DB_HOST', 'localhost')
api_key = os.environ['API_KEY']  # Raises if missing
```

---

## PART 2: AUTHENTICATION (COMPLETE FLOW)

### 2.1 LOGIN SYSTEM

```php
// auth.php - Complete authentication system

class Auth {
    private PDO $db;

    public function __construct(PDO $db) {
        $this->db = $db;
    }

    public function login(string $email, string $password): ?array {
        // Validate input
        $email = filter_var($email, FILTER_VALIDATE_EMAIL);
        if (!$email) {
            return null;
        }

        // Get user
        $stmt = $this->db->prepare("SELECT id, email, password_hash, role FROM users WHERE email = ?");
        $stmt->execute([$email]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$user || !password_verify($password, $user['password_hash'])) {
            // Log failed attempt (for security monitoring)
            error_log("Failed login attempt for: $email");
            return null;
        }

        // Regenerate session ID (prevent session fixation)
        session_regenerate_id(true);

        // Store user in session
        $_SESSION['user_id'] = $user['id'];
        $_SESSION['user_email'] = $user['email'];
        $_SESSION['user_role'] = $user['role'];
        $_SESSION['login_time'] = time();

        return $user;
    }

    public function logout(): void {
        $_SESSION = [];
        session_destroy();
    }

    public function isLoggedIn(): bool {
        return isset($_SESSION['user_id']);
    }

    public function requireAuth(): void {
        if (!$this->isLoggedIn()) {
            header('Location: /login.php');
            exit;
        }
    }

    public function requireRole(string $role): void {
        $this->requireAuth();
        if ($_SESSION['user_role'] !== $role) {
            http_response_code(403);
            die('Access denied');
        }
    }
}
```

### 2.2 PROTECTED PAGE PATTERN

```php
<?php
// dashboard.php - EVERY protected page starts like this

require_once __DIR__ . '/includes/auth.php';
require_once __DIR__ . '/includes/db.php';

session_start();

$auth = new Auth($pdo);
$auth->requireAuth();  // Redirects if not logged in

// Now safe to show protected content
$userId = $_SESSION['user_id'];
?>
<!DOCTYPE html>
<html>
<!-- Protected content here -->
</html>
```

### 2.3 API AUTHENTICATION

```php
// api/middleware.php
function requireApiAuth(): array {
    $token = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $token = str_replace('Bearer ', '', $token);

    if (empty($token)) {
        http_response_code(401);
        die(json_encode(['error' => 'Token required']));
    }

    // Validate token (JWT or database lookup)
    $user = validateToken($token);
    if (!$user) {
        http_response_code(401);
        die(json_encode(['error' => 'Invalid token']));
    }

    return $user;
}

// api/users.php
header('Content-Type: application/json');
$user = requireApiAuth();

// Now handle the API request
```

---

## PART 3: INPUT VALIDATION

### 3.1 VALIDATION PATTERNS

```php
class Validator {
    private array $errors = [];

    public function email(string $value, string $field = 'email'): ?string {
        $value = trim($value);
        if (empty($value)) {
            $this->errors[$field] = 'Email is required';
            return null;
        }
        if (strlen($value) > 254) {
            $this->errors[$field] = 'Email is too long';
            return null;
        }
        $email = filter_var($value, FILTER_VALIDATE_EMAIL);
        if (!$email) {
            $this->errors[$field] = 'Invalid email format';
            return null;
        }
        return strtolower($email);
    }

    public function password(string $value, string $field = 'password'): ?string {
        if (strlen($value) < 8) {
            $this->errors[$field] = 'Password must be at least 8 characters';
            return null;
        }
        if (strlen($value) > 72) {  // bcrypt limit
            $this->errors[$field] = 'Password is too long';
            return null;
        }
        return $value;
    }

    public function string(string $value, string $field, int $min = 1, int $max = 255): ?string {
        $value = trim($value);
        if (strlen($value) < $min) {
            $this->errors[$field] = "$field must be at least $min characters";
            return null;
        }
        if (strlen($value) > $max) {
            $this->errors[$field] = "$field must be at most $max characters";
            return null;
        }
        return $value;
    }

    public function integer($value, string $field, int $min = null, int $max = null): ?int {
        if (!is_numeric($value)) {
            $this->errors[$field] = "$field must be a number";
            return null;
        }
        $int = (int) $value;
        if ($min !== null && $int < $min) {
            $this->errors[$field] = "$field must be at least $min";
            return null;
        }
        if ($max !== null && $int > $max) {
            $this->errors[$field] = "$field must be at most $max";
            return null;
        }
        return $int;
    }

    public function hasErrors(): bool {
        return !empty($this->errors);
    }

    public function getErrors(): array {
        return $this->errors;
    }
}

// Usage
$v = new Validator();
$email = $v->email($_POST['email'] ?? '');
$password = $v->password($_POST['password'] ?? '');
$name = $v->string($_POST['name'] ?? '', 'name', 2, 100);

if ($v->hasErrors()) {
    http_response_code(400);
    echo json_encode(['errors' => $v->getErrors()]);
    exit;
}
```

### 3.2 JAVA VALIDATION

```java
public class UserDTO {
    @NotNull(message = "Email is required")
    @Email(message = "Invalid email format")
    @Size(max = 254, message = "Email is too long")
    private String email;

    @NotNull(message = "Password is required")
    @Size(min = 8, max = 72, message = "Password must be 8-72 characters")
    private String password;

    @Size(min = 2, max = 100, message = "Name must be 2-100 characters")
    private String name;
}

// Controller
@PostMapping("/users")
public ResponseEntity<?> createUser(@Valid @RequestBody UserDTO dto, BindingResult result) {
    if (result.hasErrors()) {
        Map<String, String> errors = result.getFieldErrors().stream()
            .collect(Collectors.toMap(
                FieldError::getField,
                FieldError::getDefaultMessage
            ));
        return ResponseEntity.badRequest().body(Map.of("errors", errors));
    }
    // Process valid data
}
```

---

## PART 4: DATABASE PATTERNS

### 4.1 CONNECTION & CONFIGURATION

```php
// db.php
$dsn = sprintf(
    'mysql:host=%s;dbname=%s;charset=utf8mb4',
    $_ENV['DB_HOST'],
    $_ENV['DB_NAME']
);

$pdo = new PDO($dsn, $_ENV['DB_USER'], $_ENV['DB_PASS'], [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES => false,
]);
```

```sql
-- MySQL 8.0+ uses utf8mb4 and utf8mb4_0900_ai_ci by default
CREATE DATABASE myapp CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- Table with proper constraints and indexes
CREATE TABLE users (
    id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 4.2 TRANSACTIONS

```php
// When multiple related operations must succeed or fail together
try {
    $pdo->beginTransaction();

    // Create order
    $stmt = $pdo->prepare("INSERT INTO orders (user_id, total) VALUES (?, ?)");
    $stmt->execute([$userId, $total]);
    $orderId = $pdo->lastInsertId();

    // Create order items
    $stmt = $pdo->prepare("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)");
    foreach ($items as $item) {
        $stmt->execute([$orderId, $item['product_id'], $item['quantity'], $item['price']]);
    }

    // Decrease stock
    $stmt = $pdo->prepare("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?");
    foreach ($items as $item) {
        $stmt->execute([$item['quantity'], $item['product_id'], $item['quantity']]);
        if ($stmt->rowCount() === 0) {
            throw new Exception("Insufficient stock for product {$item['product_id']}");
        }
    }

    $pdo->commit();
} catch (Exception $e) {
    $pdo->rollBack();
    throw $e;  // Re-throw or handle
}
```

### 4.3 PAGINATION

```php
function paginate(PDO $pdo, string $query, array $params, int $page = 1, int $perPage = 20): array {
    // Ensure valid values
    $page = max(1, $page);
    $perPage = min(100, max(1, $perPage));  // Max 100 per page
    $offset = ($page - 1) * $perPage;

    // Get total count
    $countQuery = preg_replace('/SELECT .* FROM/i', 'SELECT COUNT(*) FROM', $query);
    $countQuery = preg_replace('/ORDER BY .*/i', '', $countQuery);
    $stmt = $pdo->prepare($countQuery);
    $stmt->execute($params);
    $total = (int) $stmt->fetchColumn();

    // Get paginated results
    $query .= " LIMIT $perPage OFFSET $offset";
    $stmt = $pdo->prepare($query);
    $stmt->execute($params);
    $items = $stmt->fetchAll();

    return [
        'items' => $items,
        'pagination' => [
            'page' => $page,
            'per_page' => $perPage,
            'total' => $total,
            'total_pages' => (int) ceil($total / $perPage),
        ]
    ];
}

// Usage
$result = paginate($pdo,
    "SELECT * FROM products WHERE category_id = ? ORDER BY created_at DESC",
    [$categoryId],
    $page,
    20
);
```

---

## PART 5: API DESIGN

### 5.1 CONSISTENT RESPONSE FORMAT

```php
// api/response.php
function jsonResponse($data, int $status = 200): never {
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode([
        'success' => $status >= 200 && $status < 300,
        'data' => $data
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

function jsonError(string $message, string $code = 'ERROR', int $status = 400, ?string $field = null): never {
    http_response_code($status);
    header('Content-Type: application/json');
    $error = ['code' => $code, 'message' => $message];
    if ($field) $error['field'] = $field;
    echo json_encode(['success' => false, 'error' => $error], JSON_UNESCAPED_UNICODE);
    exit;
}

// Usage
jsonResponse(['user' => $user]);                           // 200 OK
jsonResponse(['user' => $user], 201);                      // 201 Created
jsonError('Email is required', 'VALIDATION_ERROR', 400, 'email');
jsonError('Not found', 'NOT_FOUND', 404);
jsonError('Server error', 'SERVER_ERROR', 500);
```

### 5.2 API ENDPOINT EXAMPLE

```php
// api/products.php
header('Content-Type: application/json');
require_once __DIR__ . '/../includes/db.php';
require_once __DIR__ . '/middleware.php';
require_once __DIR__ . '/response.php';

$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$segments = explode('/', trim($path, '/'));
$productId = $segments[2] ?? null;

try {
    switch ($method) {
        case 'GET':
            if ($productId) {
                // GET /api/products/{id}
                $stmt = $pdo->prepare("SELECT * FROM products WHERE id = ?");
                $stmt->execute([$productId]);
                $product = $stmt->fetch();
                if (!$product) jsonError('Product not found', 'NOT_FOUND', 404);
                jsonResponse($product);
            } else {
                // GET /api/products?page=1&category=5
                $page = (int) ($_GET['page'] ?? 1);
                $category = $_GET['category'] ?? null;

                $query = "SELECT * FROM products";
                $params = [];
                if ($category) {
                    $query .= " WHERE category_id = ?";
                    $params[] = $category;
                }
                $query .= " ORDER BY created_at DESC";

                $result = paginate($pdo, $query, $params, $page);
                jsonResponse($result);
            }
            break;

        case 'POST':
            requireApiAuth();
            $data = json_decode(file_get_contents('php://input'), true);
            // Validate and create...
            jsonResponse($newProduct, 201);
            break;

        case 'PUT':
            requireApiAuth();
            if (!$productId) jsonError('Product ID required', 'BAD_REQUEST', 400);
            // Validate and update...
            jsonResponse($updatedProduct);
            break;

        case 'DELETE':
            requireApiAuth();
            if (!$productId) jsonError('Product ID required', 'BAD_REQUEST', 400);
            // Delete...
            jsonResponse(['deleted' => true]);
            break;

        default:
            jsonError('Method not allowed', 'METHOD_NOT_ALLOWED', 405);
    }
} catch (Exception $e) {
    error_log($e->getMessage());
    jsonError('Internal server error', 'SERVER_ERROR', 500);
}
```

---

## PART 6: ERROR HANDLING

### 6.1 GLOBAL ERROR HANDLER

```php
// includes/error_handler.php

set_error_handler(function ($severity, $message, $file, $line) {
    throw new ErrorException($message, 0, $severity, $file, $line);
});

set_exception_handler(function (Throwable $e) {
    error_log(sprintf(
        "[%s] %s in %s:%d\nStack trace:\n%s",
        date('Y-m-d H:i:s'),
        $e->getMessage(),
        $e->getFile(),
        $e->getLine(),
        $e->getTraceAsString()
    ));

    if (php_sapi_name() === 'cli') {
        echo "Error: " . $e->getMessage() . "\n";
        exit(1);
    }

    http_response_code(500);
    if (str_contains($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json')) {
        header('Content-Type: application/json');
        echo json_encode(['success' => false, 'error' => ['code' => 'SERVER_ERROR', 'message' => 'An error occurred']]);
    } else {
        include __DIR__ . '/../templates/error_500.html';
    }
    exit;
});
```

### 6.2 TRY-CATCH PATTERNS

```php
// Specific exceptions for different error types
class ValidationException extends Exception {}
class NotFoundException extends Exception {}
class AuthException extends Exception {}

// Usage
try {
    $user = $userService->findById($id);
    if (!$user) {
        throw new NotFoundException("User not found");
    }
} catch (NotFoundException $e) {
    jsonError($e->getMessage(), 'NOT_FOUND', 404);
} catch (ValidationException $e) {
    jsonError($e->getMessage(), 'VALIDATION_ERROR', 400);
} catch (Exception $e) {
    error_log($e->getMessage());
    jsonError('An error occurred', 'SERVER_ERROR', 500);
}
```

---

## PART 7: TESTING

### 7.1 PHP TEST TEMPLATE

```php
<?php
// tests/UserTest.php
require_once __DIR__ . '/../src/User.php';

class TestRunner {
    private int $passed = 0;
    private int $failed = 0;
    private array $failures = [];

    public function test(string $name, callable $fn): void {
        try {
            $fn();
            $this->passed++;
            echo "✓ $name\n";
        } catch (Throwable $e) {
            $this->failed++;
            $this->failures[] = "$name: " . $e->getMessage();
            echo "✗ $name\n";
        }
    }

    public function assertEquals($expected, $actual, string $message = ''): void {
        if ($expected !== $actual) {
            throw new Exception($message ?: "Expected " . var_export($expected, true) . ", got " . var_export($actual, true));
        }
    }

    public function assertTrue($value, string $message = ''): void {
        if ($value !== true) {
            throw new Exception($message ?: "Expected true, got " . var_export($value, true));
        }
    }

    public function assertFalse($value, string $message = ''): void {
        if ($value !== false) {
            throw new Exception($message ?: "Expected false, got " . var_export($value, true));
        }
    }

    public function summary(): void {
        echo "\n" . str_repeat('=', 50) . "\n";
        echo "Passed: {$this->passed} | Failed: {$this->failed}\n";
        if ($this->failures) {
            echo "\nFailures:\n";
            foreach ($this->failures as $f) echo "  - $f\n";
        }
        exit($this->failed > 0 ? 1 : 0);
    }
}

// Tests
$t = new TestRunner();

$t->test('validateEmail accepts valid email', function() use ($t) {
    $v = new Validator();
    $result = $v->email('test@example.com');
    $t->assertEquals('test@example.com', $result);
    $t->assertFalse($v->hasErrors());
});

$t->test('validateEmail rejects invalid email', function() use ($t) {
    $v = new Validator();
    $result = $v->email('invalid');
    $t->assertEquals(null, $result);
    $t->assertTrue($v->hasErrors());
});

$t->test('validateEmail rejects empty', function() use ($t) {
    $v = new Validator();
    $result = $v->email('');
    $t->assertEquals(null, $result);
    $t->assertTrue($v->hasErrors());
});

$t->summary();
```

### 7.2 PYTHON TEST

```python
import pytest
from validator import Validator

class TestValidator:
    def test_valid_email(self):
        v = Validator()
        result = v.email('test@example.com')
        assert result == 'test@example.com'
        assert not v.has_errors()

    def test_invalid_email(self):
        v = Validator()
        result = v.email('invalid')
        assert result is None
        assert v.has_errors()

    def test_password_min_length(self):
        v = Validator()
        result = v.password('short')
        assert result is None
        assert 'password' in v.get_errors()

# Run: pytest -v tests/
```

### 7.3 UI TESTING

```bash
# Use the verification script
python /opt/codehero/scripts/verify_ui.py https://127.0.0.1:9867/myproject/

# Outputs:
# - screenshot_desktop.png (1920x1080)
# - screenshot_mobile.png (375x667)
# - Console errors
# - Failed requests
# - All links

# View screenshots
Read /tmp/screenshot_desktop.png
Read /tmp/screenshot_mobile.png
```

---

## PART 8: UI RULES

### 8.1 TAILWIND ESSENTIALS

```html
<!-- Grid MUST have columns -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

<!-- Flex MUST have direction -->
<div class="flex flex-col md:flex-row gap-4">

<!-- Dark backgrounds need light text -->
<div class="bg-gray-800 text-white">

<!-- Always include responsive breakpoints -->
<div class="w-full md:w-1/2 lg:w-1/3">
```

### 8.2 SIZING REFERENCE

| Element | Size |
|---------|------|
| Header | 60-80px |
| Card padding | 16-24px |
| Gaps | 16-24px |
| Small icons | 24-32px |
| Large icons | 40-48px |
| H1 | 2-3rem |
| Body text | 1rem |

**Avoid:** padding > 32px, icons > 64px, gaps > 32px

### 8.3 ACCESSIBILITY

```html
<!-- Images need alt text -->
<img src="photo.jpg" alt="Description of image">

<!-- Forms need labels -->
<label for="email">Email</label>
<input id="email" type="email">

<!-- Buttons need context -->
<button aria-label="Close dialog">×</button>

<!-- Skip link for keyboard users -->
<a href="#main" class="sr-only focus:not-sr-only">Skip to content</a>
```

### 8.4 LINKS

**Always use relative paths** (projects are in subfolders):

```html
<!-- WRONG - Goes to server root -->
<a href="/about.php">

<!-- CORRECT - Relative to current page -->
<a href="about.php">
<a href="../index.php">
```

---

## PART 9: JAVA/SPRING BOOT

### 9.1 PROJECT STRUCTURE

```
src/main/java/com/example/
├── controller/          # REST endpoints
├── service/             # Business logic
├── repository/          # Data access
├── model/               # JPA entities
├── dto/                 # Request/Response objects
├── config/              # Configuration
├── exception/           # Custom exceptions
└── MyApplication.java
```

### 9.2 COMPLETE CRUD EXAMPLE

```java
// Entity
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 254)
    private String email;

    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(name = "created_at")
    private Instant createdAt = Instant.now();
}

// Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);
}

// Service
@Service
@Transactional
public class UserService {
    private final UserRepository repo;
    private final PasswordEncoder encoder;

    public User create(CreateUserDTO dto) {
        if (repo.existsByEmail(dto.getEmail())) {
            throw new ValidationException("Email already exists");
        }
        User user = new User();
        user.setEmail(dto.getEmail().toLowerCase().trim());
        user.setPasswordHash(encoder.encode(dto.getPassword()));
        user.setName(dto.getName().trim());
        return repo.save(user);
    }

    public User getById(Long id) {
        return repo.findById(id)
            .orElseThrow(() -> new NotFoundException("User not found"));
    }
}

// Controller
@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserService service;

    @PostMapping
    public ResponseEntity<User> create(@Valid @RequestBody CreateUserDTO dto) {
        User user = service.create(dto);
        return ResponseEntity.status(HttpStatus.CREATED).body(user);
    }

    @GetMapping("/{id}")
    public User getById(@PathVariable Long id) {
        return service.getById(id);
    }
}

// Exception Handler
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<Map<String, Object>> handleValidation(ValidationException e) {
        return ResponseEntity.badRequest().body(Map.of(
            "success", false,
            "error", Map.of("code", "VALIDATION_ERROR", "message", e.getMessage())
        ));
    }

    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<Map<String, Object>> handleNotFound(NotFoundException e) {
        return ResponseEntity.status(404).body(Map.of(
            "success", false,
            "error", Map.of("code", "NOT_FOUND", "message", e.getMessage())
        ));
    }
}
```

---

## PART 10: MOBILE DEVELOPMENT

### 10.1 ANDROID (KOTLIN)

```kotlin
// Security - Encrypted storage
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val securePrefs = EncryptedSharedPreferences.create(
    context, "secure_prefs", masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)

// Save/retrieve tokens
securePrefs.edit().putString("auth_token", token).apply()
val token = securePrefs.getString("auth_token", null)

// ViewModel pattern
class UserViewModel(private val repo: UserRepository) : ViewModel() {
    private val _user = MutableLiveData<Result<User>>()
    val user: LiveData<Result<User>> = _user

    fun load(id: String) = viewModelScope.launch {
        _user.value = repo.getUser(id)
    }
}

// Fragment observation
viewModel.user.observe(viewLifecycleOwner) { result ->
    when (result) {
        is Result.Success -> showUser(result.data)
        is Result.Error -> showError(result.message)
    }
}
```

### 10.2 REACT NATIVE

```typescript
// Secure storage
import * as SecureStore from 'expo-secure-store';

export const storage = {
    async setToken(token: string) {
        await SecureStore.setItemAsync('auth_token', token);
    },
    async getToken(): Promise<string | null> {
        return SecureStore.getItemAsync('auth_token');
    },
    async clearToken() {
        await SecureStore.deleteItemAsync('auth_token');
    }
};

// API client with auth
const api = {
    async request(endpoint: string, options: RequestInit = {}) {
        const token = await storage.getToken();
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(token && { Authorization: `Bearer ${token}` }),
                ...options.headers,
            },
        });
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return response.json();
    },
    getUser: (id: string) => api.request(`/users/${id}`),
    updateUser: (id: string, data: object) =>
        api.request(`/users/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
};
```

### 10.3 CAPACITOR

```typescript
// capacitor.config.ts
const config: CapacitorConfig = {
    appId: 'com.example.app',
    appName: 'My App',
    webDir: 'dist',
    server: { androidScheme: 'https' }
};

// Commands
// npm run build && npx cap sync
// npx cap run android -l  (live reload)
// npx cap open android    (open in Android Studio)

// Plugins
import { Camera, CameraResultType } from '@capacitor/camera';
import { Preferences } from '@capacitor/preferences';

const photo = await Camera.getPhoto({ resultType: CameraResultType.Uri });
await Preferences.set({ key: 'user', value: JSON.stringify(user) });
const { value } = await Preferences.get({ key: 'user' });
```

---

## PART 11: SERVER & PROJECT SETUP

### 11.1 SERVER INFO

| Tool | Version |
|------|---------|
| Ubuntu | 24.04 |
| PHP | 8.3 |
| Node.js | 22.x |
| MySQL | 8.0 |
| Python | 3.12 |

**Ports:** Admin=9453, Projects=9867, MySQL=3306

### 11.2 PROJECT STRUCTURES

```
PHP Web Project:
/var/www/projects/mysite/
├── index.php
├── assets/{css,js,images,lib}/
├── includes/{db.php,auth.php,functions.php}
├── api/
├── templates/
└── tests/

Python API:
/opt/apps/myapi/
├── app.py
├── requirements.txt
├── .env
├── src/{routes,services,models}/
└── tests/

Vue/React App:
/opt/apps/myapp/
├── src/{components,views,stores,services}/
├── package.json
└── vite.config.js
```

---

## PART 12: DESIGN STANDARDS

### 12.1 SPACING SYSTEM (4px Grid)

Use multiples of 4px for ALL spacing:

| Token | Value | Use |
|-------|-------|-----|
| xs | 4px | Tight gaps, icon padding |
| sm | 8px | Related elements |
| md | 16px | Section padding, card gaps |
| lg | 24px | Section separators |
| xl | 32px | Major sections |
| 2xl | 48px | Page sections |

**Tailwind classes:** `gap-1` (4px), `gap-2` (8px), `gap-4` (16px), `gap-6` (24px), `gap-8` (32px)

**Rule:** Internal spacing ≤ External spacing
- Card content padding (16px) < Gap between cards (24px)
- Button text padding (8px) < Button margins (16px)

### 12.2 COLOR SYSTEM (60-30-10 Rule)

| Role | % | Tailwind | Use |
|------|---|----------|-----|
| **Primary** | 60% | `gray-50`, `white` | Backgrounds |
| **Secondary** | 30% | `gray-100-200`, `slate-800` | Cards, headers |
| **Accent** | 10% | `blue-600`, `indigo-600` | CTAs, links |

**Semantic Colors:**

| Purpose | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | `bg-gray-50` | `bg-gray-900` |
| Surface/Card | `bg-white` | `bg-gray-800` |
| Text Primary | `text-gray-900` | `text-white` |
| Text Secondary | `text-gray-600` | `text-gray-400` |
| Border | `border-gray-200` | `border-gray-700` |
| Accent/CTA | `bg-blue-600 text-white` | `bg-blue-500 text-white` |
| Success | `text-green-600` | `text-green-400` |
| Error | `text-red-600` | `text-red-400` |
| Warning | `text-amber-600` | `text-amber-400` |

**Avoid:**
- Pure black (`#000`) → Use `gray-900` or `slate-900`
- Pure white (`#fff`) for large areas → Use `gray-50`
- More than 3 accent colors

### 12.3 TYPOGRAPHY

| Element | Class | Size | Line Height |
|---------|-------|------|-------------|
| H1 | `text-4xl font-bold` | 36px | tight |
| H2 | `text-3xl font-semibold` | 30px | tight |
| H3 | `text-2xl font-semibold` | 24px | snug |
| H4 | `text-xl font-medium` | 20px | snug |
| Body | `text-base` | 16px | relaxed |
| Small | `text-sm` | 14px | normal |
| Caption | `text-xs` | 12px | normal |

**Rules:**
- Body text: `leading-relaxed` (1.625) for readability
- Headings: `leading-tight` (1.25) for compactness
- Maximum line width: `max-w-prose` (65 characters)

### 12.4 BORDER RADIUS

| Token | Class | Value | Use |
|-------|-------|-------|-----|
| None | `rounded-none` | 0 | Tables, full-width |
| Small | `rounded` | 4px | Inputs, badges |
| Medium | `rounded-md` | 6px | Buttons |
| Large | `rounded-lg` | 8px | Cards |
| XL | `rounded-xl` | 12px | Modals, large cards |
| Full | `rounded-full` | 9999px | Avatars, pills |

**Nested Rule:** Outer radius = Inner radius + Padding
- Card with 16px padding and inner 8px radius → outer 24px radius

### 12.5 SHADOWS (Elevation)

| Level | Class | Use |
|-------|-------|-----|
| 0 | `shadow-none` | Flat elements |
| 1 | `shadow-sm` | Subtle lift (cards) |
| 2 | `shadow` | Standard elevation |
| 3 | `shadow-md` | Dropdowns, popovers |
| 4 | `shadow-lg` | Modals, dialogs |
| 5 | `shadow-xl` | Important overlays |

**Dark Mode:** Use lighter surface colors instead of shadows
- `dark:bg-gray-700` instead of `dark:shadow-lg`

### 12.6 COMPONENT PATTERNS

#### Buttons

```html
<!-- Primary -->
<button class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors">
  Primary Action
</button>

<!-- Secondary -->
<button class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-md transition-colors">
  Secondary
</button>

<!-- Ghost -->
<button class="px-4 py-2 hover:bg-gray-100 text-gray-600 font-medium rounded-md transition-colors">
  Ghost
</button>

<!-- Disabled -->
<button class="px-4 py-2 bg-gray-200 text-gray-400 font-medium rounded-md cursor-not-allowed" disabled>
  Disabled
</button>
```

**Sizes:**
- Small: `px-3 py-1.5 text-sm`
- Medium: `px-4 py-2 text-base` (default)
- Large: `px-6 py-3 text-lg`

#### Cards

```html
<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
  <h3 class="text-lg font-semibold text-gray-900 mb-2">Card Title</h3>
  <p class="text-gray-600 mb-4">Card content goes here.</p>
  <button class="text-blue-600 hover:text-blue-700 font-medium">Action →</button>
</div>
```

#### Form Inputs

```html
<div class="space-y-1">
  <label for="email" class="block text-sm font-medium text-gray-700">Email</label>
  <input
    type="email"
    id="email"
    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
           focus:ring-2 focus:ring-blue-500 focus:border-blue-500
           placeholder-gray-400"
    placeholder="you@example.com"
  >
  <p class="text-sm text-gray-500">We'll never share your email.</p>
</div>

<!-- Error state -->
<input class="... border-red-500 focus:ring-red-500 focus:border-red-500">
<p class="text-sm text-red-600">Please enter a valid email.</p>
```

**Input Sizes:**
- Height: 40-48px (py-2 to py-3)
- Consistent across all inputs, selects, buttons in same row

### 12.7 RESPONSIVE PATTERNS

```html
<!-- Mobile-first grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

<!-- Flexible container -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

<!-- Responsive text -->
<h1 class="text-2xl md:text-3xl lg:text-4xl font-bold">
```

### 12.8 DARK MODE

Always support dark mode with `dark:` variants:

```html
<div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  <p class="text-gray-600 dark:text-gray-400">Secondary text</p>
  <div class="border border-gray-200 dark:border-gray-700">...</div>
</div>
```

---

## FINAL CHECKLIST

### Before Every Commit

**Security:**
- [ ] All SQL uses prepared statements
- [ ] All output is escaped (htmlspecialchars/DOMPurify)
- [ ] Passwords hashed with bcrypt
- [ ] Credentials in .env (not in code)
- [ ] CSRF tokens on all forms
- [ ] Session cookies are secure (httpOnly, secure, sameSite)
- [ ] Auth check on every protected page/API
- [ ] Rate limiting on login/sensitive endpoints
- [ ] File uploads validated and sanitized

**Data:**
- [ ] Input validated before processing
- [ ] Transactions for related DB operations
- [ ] Null checks before accessing properties
- [ ] Pagination on list endpoints (max 100)
- [ ] Dates stored in UTC

**Code:**
- [ ] Error handling with proper logging
- [ ] Consistent API response format
- [ ] Tests written and passing
- [ ] No TODO/FIXME left in code

**UI:**
- [ ] Screenshots reviewed (desktop + mobile)
- [ ] Zero console errors
- [ ] Zero server log errors
- [ ] All links work
- [ ] Grids have explicit columns
- [ ] Responsive breakpoints present
- [ ] Alt text on images

**Design:**
- [ ] 4px/8px grid for all spacing
- [ ] 60-30-10 color distribution (primary/secondary/accent)
- [ ] No pure black (#000) or pure white (#fff) on large areas
- [ ] Consistent border radius (see 12.4)
- [ ] Dark mode variants on all color classes
- [ ] Typography hierarchy maintained (H1→H4, body, small)
- [ ] Buttons follow standard patterns (primary/secondary/ghost)

---

> **Philosophy:** Write code as if the person maintaining it is a violent psychopath who knows where you live.
