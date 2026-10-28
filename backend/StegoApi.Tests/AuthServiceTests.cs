using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using StegoApi.Data;
using StegoApi.Models.DTOs;
using StegoApi.Services.Implementations;
using StegoApi.Utilities;
using Xunit;

namespace StegoApi.Tests;

public class AuthServiceTests
{
    private readonly IConfiguration _configuration;

    public AuthServiceTests()
    {
        var inMemorySettings = new Dictionary<string, string?>
        {
            {"JwtSettings:Secret", "TestSuperSecretKeyForSteganographySystemUnitTests2026!"},
            {"JwtSettings:Issuer", "StegoApiTest"},
            {"JwtSettings:Audience", "StegoClientTest"},
            {"JwtSettings:ExpiryHours", "12"}
        };

        _configuration = new ConfigurationBuilder()
            .AddInMemoryCollection(inMemorySettings)
            .Build();
    }

    private ApplicationDbContext CreateInMemoryDbContext()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        return new ApplicationDbContext(options);
    }

    private AuthService CreateAuthService(ApplicationDbContext context)
    {
        var tokenService = new TokenService(_configuration);
        var keyVaultService = new KeyVaultService(context, _configuration);
        return new AuthService(context, tokenService, keyVaultService);
    }

    [Fact]
    public void PasswordHasher_Hashes_And_Verifies_Successfully()
    {
        string rawPassword = "StrongP@ssw0rd2026!";
        var (hash, salt) = PasswordHasher.HashPassword(rawPassword);

        Assert.False(string.IsNullOrWhiteSpace(hash));
        Assert.False(string.IsNullOrWhiteSpace(salt));
        Assert.NotEqual(rawPassword, hash);

        bool isValid = PasswordHasher.VerifyPassword(rawPassword, hash, salt);
        Assert.True(isValid);
    }

    [Fact]
    public void PasswordHasher_Rejects_Wrong_Password()
    {
        string rawPassword = "CorrectPassword123";
        var (hash, salt) = PasswordHasher.HashPassword(rawPassword);

        bool isValid = PasswordHasher.VerifyPassword("WrongPassword456", hash, salt);
        Assert.False(isValid);
    }

    [Fact]
    public void TokenService_Generates_Valid_Jwt_With_Claims()
    {
        var tokenService = new TokenService(_configuration);

        var user = new Models.Entities.User
        {
            Id = Guid.NewGuid(),
            Username = "alice_crypto",
            Email = "alice@example.com"
        };

        var (token, expiresAt) = tokenService.GenerateToken(user);

        Assert.False(string.IsNullOrEmpty(token));
        Assert.True(expiresAt > DateTime.UtcNow);

        // Parse token and inspect claims
        var handler = new JwtSecurityTokenHandler();
        var jwt = handler.ReadJwtToken(token);

        Assert.Equal("StegoApiTest", jwt.Issuer);

        var idClaim = jwt.Claims.FirstOrDefault(c => c.Type == ClaimTypes.NameIdentifier || c.Type == "nameid" || c.Type == "sub");
        Assert.NotNull(idClaim);
        Assert.Equal(user.Id.ToString(), idClaim.Value);

        var nameClaim = jwt.Claims.FirstOrDefault(c => c.Type == ClaimTypes.Name || c.Type == "unique_name" || c.Type == "name");
        Assert.NotNull(nameClaim);
        Assert.Equal("alice_crypto", nameClaim.Value);

        var emailClaim = jwt.Claims.FirstOrDefault(c => c.Type == ClaimTypes.Email || c.Type == "email");
        Assert.NotNull(emailClaim);
        Assert.Equal("alice@example.com", emailClaim.Value);
    }

    [Fact]
    public async Task RegisterAsync_Creates_User_And_Returns_Valid_AuthResponse()
    {
        using var context = CreateInMemoryDbContext();
        var authService = CreateAuthService(context);

        var request = new RegisterRequestDto
        {
            Username = "bob_stego",
            Email = "bob@example.com",
            Password = "SecurePassword123!"
        };

        var (success, errorMessage, response) = await authService.RegisterAsync(request);

        Assert.True(success);
        Assert.Null(errorMessage);
        Assert.NotNull(response);
        Assert.Equal("bob_stego", response.Username);
        Assert.Equal("bob@example.com", response.Email);
        Assert.False(string.IsNullOrEmpty(response.Token));

        // Verify stored in DB
        var userInDb = await context.Users.FirstOrDefaultAsync(u => u.Email == "bob@example.com");
        Assert.NotNull(userInDb);
        Assert.True(PasswordHasher.VerifyPassword("SecurePassword123!", userInDb.PasswordHash, userInDb.PasswordSalt));
    }

    [Fact]
    public async Task RegisterAsync_Rejects_Duplicate_Email()
    {
        using var context = CreateInMemoryDbContext();
        var authService = CreateAuthService(context);

        var request1 = new RegisterRequestDto
        {
            Username = "user1",
            Email = "duplicate@example.com",
            Password = "Password123!"
        };
        await authService.RegisterAsync(request1);

        var request2 = new RegisterRequestDto
        {
            Username = "user2",
            Email = "duplicate@example.com",
            Password = "Password456!"
        };
        var (success, errorMessage, response) = await authService.RegisterAsync(request2);

        Assert.False(success);
        Assert.Contains("email address already exists", errorMessage);
        Assert.Null(response);
    }

    [Fact]
    public async Task LoginAsync_Succeeds_With_Valid_Credentials()
    {
        using var context = CreateInMemoryDbContext();
        var authService = CreateAuthService(context);

        await authService.RegisterAsync(new RegisterRequestDto
        {
            Username = "charlie",
            Email = "charlie@example.com",
            Password = "SecretPassword123!"
        });

        var (success, errorMessage, response) = await authService.LoginAsync(new LoginRequestDto
        {
            Email = "charlie@example.com",
            Password = "SecretPassword123!"
        });

        Assert.True(success);
        Assert.Null(errorMessage);
        Assert.NotNull(response);
        Assert.Equal("charlie", response.Username);
        Assert.False(string.IsNullOrEmpty(response.Token));
    }

    [Fact]
    public async Task LoginAsync_Rejects_Incorrect_Password()
    {
        using var context = CreateInMemoryDbContext();
        var authService = CreateAuthService(context);

        await authService.RegisterAsync(new RegisterRequestDto
        {
            Username = "david",
            Email = "david@example.com",
            Password = "SecretPassword123!"
        });

        var (success, errorMessage, response) = await authService.LoginAsync(new LoginRequestDto
        {
            Email = "david@example.com",
            Password = "WrongPassword999!"
        });

        Assert.False(success);
        Assert.Equal("Invalid email or password.", errorMessage);
        Assert.Null(response);
    }

    [Fact]
    public async Task GetUserProfileAsync_Returns_Accurate_Metadata()
    {
        using var context = CreateInMemoryDbContext();
        var authService = CreateAuthService(context);

        var (regSuccess, _, regResponse) = await authService.RegisterAsync(new RegisterRequestDto
        {
            Username = "eve_evaluator",
            Email = "eve@example.com",
            Password = "Password123!"
        });

        Assert.True(regSuccess);
        var profile = await authService.GetUserProfileAsync(regResponse!.UserId);

        Assert.NotNull(profile);
        Assert.Equal("eve_evaluator", profile.Username);
        Assert.Equal("eve@example.com", profile.Email);
        Assert.Equal(0, profile.OperationCount);
        // Automated key generation ensures newly registered user has an active RSA-4096 key
        Assert.True(profile.HasRsaKey);
        Assert.Equal(4096, profile.ActiveKeySizeBits);
    }
}
