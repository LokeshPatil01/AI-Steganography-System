using Microsoft.EntityFrameworkCore;
using StegoApi.Data;
using StegoApi.Models.DTOs;
using StegoApi.Models.Entities;
using StegoApi.Services.Interfaces;
using StegoApi.Utilities;

namespace StegoApi.Services.Implementations;

public class AuthService : IAuthService
{
    private readonly ApplicationDbContext _context;
    private readonly ITokenService _tokenService;
    private readonly IKeyVaultService _keyVaultService;

    public AuthService(ApplicationDbContext context, ITokenService tokenService, IKeyVaultService keyVaultService)
    {
        _context = context;
        _tokenService = tokenService;
        _keyVaultService = keyVaultService;
    }

    public async Task<(bool Success, string? ErrorMessage, AuthResponseDto? Response)> RegisterAsync(RegisterRequestDto request)
    {
        string normalizedEmail = request.Email.Trim().ToLowerInvariant();
        string normalizedUsername = request.Username.Trim();

        // Check if email already exists
        if (await _context.Users.AnyAsync(u => u.Email.ToLower() == normalizedEmail))
        {
            return (false, "An account with this email address already exists.", null);
        }

        // Check if username already exists
        if (await _context.Users.AnyAsync(u => u.Username.ToLower() == normalizedUsername.ToLower()))
        {
            return (false, "This username is already taken. Please choose another.", null);
        }

        // Hash password securely with salt
        var (hash, salt) = PasswordHasher.HashPassword(request.Password);

        var user = new User
        {
            Username = normalizedUsername,
            Email = normalizedEmail,
            PasswordHash = hash,
            PasswordSalt = salt,
            CreatedAt = DateTime.UtcNow,
            IsActive = true
        };

        _context.Users.Add(user);
        await _context.SaveChangesAsync();

        // AUTOMATED KEY GENERATION:
        // Automatically provision an RSA-4096 key pair and encrypt the private key at rest
        await _keyVaultService.GenerateAndStoreUserKeyAsync(user.Id, user.PasswordHash);

        // Generate JWT token
        var (token, expiresAt) = _tokenService.GenerateToken(user);

        var response = new AuthResponseDto
        {
            Token = token,
            UserId = user.Id,
            Username = user.Username,
            Email = user.Email,
            ExpiresAt = expiresAt
        };

        return (true, null, response);
    }

    public async Task<(bool Success, string? ErrorMessage, AuthResponseDto? Response)> LoginAsync(LoginRequestDto request)
    {
        string normalizedEmail = request.Email.Trim().ToLowerInvariant();

        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Email.ToLower() == normalizedEmail);

        if (user == null)
        {
            // Generic message to prevent user enumeration
            return (false, "Invalid email or password.", null);
        }

        if (!user.IsActive)
        {
            return (false, "This account is inactive. Please contact support.", null);
        }

        // Verify password hash
        bool isValid = PasswordHasher.VerifyPassword(request.Password, user.PasswordHash, user.PasswordSalt);
        if (!isValid)
        {
            return (false, "Invalid email or password.", null);
        }

        // Generate JWT token
        var (token, expiresAt) = _tokenService.GenerateToken(user);

        var response = new AuthResponseDto
        {
            Token = token,
            UserId = user.Id,
            Username = user.Username,
            Email = user.Email,
            ExpiresAt = expiresAt
        };

        return (true, null, response);
    }

    public async Task<UserProfileDto?> GetUserProfileAsync(Guid userId)
    {
        var user = await _context.Users
            .Include(u => u.Keys)
            .Include(u => u.Operations)
            .FirstOrDefaultAsync(u => u.Id == userId);

        if (user == null)
            return null;

        var activeKey = user.Keys.FirstOrDefault(k => !k.IsRevoked);

        return new UserProfileDto
        {
            UserId = user.Id,
            Username = user.Username,
            Email = user.Email,
            CreatedAt = user.CreatedAt,
            HasRsaKey = activeKey != null,
            ActiveKeySizeBits = activeKey?.KeySizeBits ?? 0,
            KeyFingerprint = activeKey?.KeyFingerprint,
            OperationCount = user.Operations.Count
        };
    }
}
