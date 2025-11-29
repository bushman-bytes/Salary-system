# Security Features

This document outlines the security features implemented in the Salary Management System.

## Implemented Security Features

### 1. Rate Limiting
- **Login Endpoint**: Limited to 5 attempts per minute per IP address
- **Protection**: Prevents brute force attacks on authentication endpoints
- **Implementation**: Using `slowapi` library

### 2. CORS (Cross-Origin Resource Sharing)
- **Configuration**: Restricted to specific allowed origins
- **Development**: Allows localhost ports (8000, 3000)
- **Production**: Set via `ALLOWED_ORIGINS` environment variable (comma-separated list)
- **Example**: `ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com`

### 3. Security Headers
The following security headers are automatically added to all responses:
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking attacks
- `X-XSS-Protection: 1; mode=block` - Enables XSS filtering
- `Strict-Transport-Security` - Forces HTTPS connections
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer information
- `Permissions-Policy` - Restricts browser features (geolocation, microphone, camera)

### 4. Error Message Security
- Generic error messages for authentication failures
- No exposure of sensitive information in error responses
- Consistent error handling across all endpoints

### 5. Environment Variable Validation
- Database connection string validation
- Required environment variables checked at startup
- Clear error messages if configuration is missing

### 6. Input Validation
- Pydantic models for request validation
- Type checking and format validation
- SQL injection protection via SQLAlchemy ORM

## Configuration

### Environment Variables

#### Required
- `DATABASE_URL`: PostgreSQL connection string (required)

#### Optional (for CORS)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins for CORS
  - Example: `ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com`
  - If not set, defaults to localhost for development

#### Optional (for notifications)
- `EMAIL_HOST`: SMTP server hostname
- `EMAIL_PORT`: SMTP server port
- `EMAIL_USER`: Email username
- `EMAIL_PASSWORD`: Email password
- `EMAIL_FROM`: Sender email address
- `WHATSAPP_ACCOUNT_SID`: Twilio account SID
- `WHATSAPP_AUTH_TOKEN`: Twilio auth token
- `WHATSAPP_FROM_NUMBER`: Twilio phone number

## Production Deployment Checklist

- [ ] Set `ALLOWED_ORIGINS` environment variable with your production domain(s)
- [ ] Ensure `DATABASE_URL` is set and valid
- [ ] Verify HTTPS is enabled (Vercel handles this automatically)
- [ ] Review and update rate limiting thresholds if needed
- [ ] Remove any hardcoded credentials or secrets
- [ ] Enable database connection encryption (SSL)
- [ ] Regularly update dependencies for security patches

## Security Best Practices

1. **Never commit secrets**: Use environment variables for all sensitive data
2. **Use HTTPS**: Always use HTTPS in production (Vercel provides this automatically)
3. **Regular updates**: Keep dependencies updated to patch security vulnerabilities
4. **Monitor logs**: Regularly review application logs for suspicious activity
5. **Strong authentication**: Consider implementing stronger authentication (JWT tokens, OAuth) for production
6. **Database security**: Use connection pooling and SSL for database connections
7. **Input sanitization**: All user inputs are validated through Pydantic models

## Rate Limiting Details

- **Login endpoint**: 5 requests per minute per IP
- **Other endpoints**: No rate limiting by default (can be added as needed)

To modify rate limits, edit the `@limiter.limit()` decorator in `main.py`.

## CORS Configuration

In production, set the `ALLOWED_ORIGINS` environment variable in Vercel:

1. Go to your Vercel project settings
2. Navigate to "Environment Variables"
3. Add `ALLOWED_ORIGINS` with your domain(s):
   ```
   ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

If `ALLOWED_ORIGINS` is not set, the application defaults to allowing localhost origins (development mode).

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly. Do not create public GitHub issues for security vulnerabilities.
