using System.Security.Cryptography;
using System.Text;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using StegoApi.Data;
using StegoApi.Models.DTOs;
using StegoApi.Models.Entities;
using StegoApi.Services.Implementations;
using Xunit;

namespace StegoApi.Tests;

public class KeyVaultServiceTests
{
    private readonly IConfiguration _configuration;

    public KeyVaultServiceTests()
    {
        var inMemorySettings = new Dictionary<string, string?>
        {
            {"JwtSettings:Secret", "SuperSecretMasterKeyVaultKeyForTestingPurposes2026!"},
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

    [Fact]
    public async Task GenerateAndStoreUserKeyAsync_Generates_Valid_Rsa4096_With_Encrypted_Private_Key()
    {
        using var context = CreateInMemoryDbContext();
        var keyVaultService = new KeyVaultService(context, _configuration);

        var userId = Guid.NewGuid();
        string userPasswordHash = "dummy_hashed_password_for_alice_2026";

        var userKey = await keyVaultService.GenerateAndStoreUserKeyAsync(userId, userPasswordHash);

        Assert.NotNull(userKey);
        Assert.Equal(userId, userKey.UserId);
        Assert.Equal(4096, userKey.KeySizeBits);
        Assert.False(userKey.IsRevoked);

        // Public key checks
        Assert.StartsWith("-----BEGIN PUBLIC KEY-----", userKey.PublicKeyPem);
        Assert.Contains("-----END PUBLIC KEY-----", userKey.PublicKeyPem);
        Assert.StartsWith("SHA256:", userKey.KeyFingerprint);

        // Security check: Private key must NOT be stored in plaintext
        Assert.DoesNotContain("-----BEGIN RSA PRIVATE KEY-----", userKey.EncryptedPrivateKeyPem);
        Assert.DoesNotContain("-----BEGIN PRIVATE KEY-----", userKey.EncryptedPrivateKeyPem);
        Assert.False(string.IsNullOrEmpty(userKey.KeyIv));
        Assert.False(string.IsNullOrEmpty(userKey.KeyTag));

        // Stored in database
        var stored = await context.UserKeys.FirstOrDefaultAsync(k => k.UserId == userId);
        Assert.NotNull(stored);
    }

    [Fact]
    public async Task DecryptUserPrivateKeyPemAsync_Recovers_Functional_Rsa_Private_Key()
    {
        using var context = CreateInMemoryDbContext();
        var keyVaultService = new KeyVaultService(context, _configuration);

        var userId = Guid.NewGuid();
        string userPasswordHash = "hashed_password_bob_32bytes_sample";

        var originalKey = await keyVaultService.GenerateAndStoreUserKeyAsync(userId, userPasswordHash);

        // Decrypt with correct credentials
        string? decryptedPrivatePem = await keyVaultService.DecryptUserPrivateKeyPemAsync(userId, userPasswordHash);

        Assert.NotNull(decryptedPrivatePem);
        Assert.StartsWith("-----BEGIN PRIVATE KEY-----", decryptedPrivatePem);

        // Verify cryptographic functionality by importing into RSA and signing/verifying a message
        using var rsaPriv = RSA.Create();
        rsaPriv.ImportFromPem(decryptedPrivatePem);

        using var rsaPub = RSA.Create();
        rsaPub.ImportFromPem(originalKey.PublicKeyPem);

        byte[] testData = Encoding.UTF8.GetBytes("Steganography research verification payload 2026");
        byte[] signature = rsaPriv.SignData(testData, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);

        bool verified = rsaPub.VerifyData(testData, signature, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
        Assert.True(verified, "Decrypted private key must produce valid signatures verifiable by the public key");
    }

    [Fact]
    public async Task DecryptUserPrivateKeyPemAsync_Fails_When_Password_Is_Incorrect()
    {
        using var context = CreateInMemoryDbContext();
        var keyVaultService = new KeyVaultService(context, _configuration);

        var userId = Guid.NewGuid();
        string userPasswordHash = "correct_user_password_hash";

        await keyVaultService.GenerateAndStoreUserKeyAsync(userId, userPasswordHash);

        // Attempt decryption with wrong credentials
        string? decryptedPrivatePem = await keyVaultService.DecryptUserPrivateKeyPemAsync(userId, "wrong_password_hash");

        Assert.Null(decryptedPrivatePem);
    }

    [Fact]
    public async Task RegenerateUserKeyAsync_Revokes_Previous_Key_And_Issues_New_One()
    {
        using var context = CreateInMemoryDbContext();
        var keyVaultService = new KeyVaultService(context, _configuration);

        var userId = Guid.NewGuid();
        string passwordHash = "user_password_hash_for_rotation";

        var key1 = await keyVaultService.GenerateAndStoreUserKeyAsync(userId, passwordHash);
        Assert.False(key1.IsRevoked);

        var key2 = await keyVaultService.RegenerateUserKeyAsync(userId, passwordHash);

        Assert.NotNull(key2);
        Assert.False(key2.IsRevoked);
        Assert.NotEqual(key1.KeyFingerprint, key2.KeyFingerprint);

        // Verify key1 is now revoked in database
        var revokedKey1 = await context.UserKeys.FindAsync(key1.Id);
        Assert.NotNull(revokedKey1);
        Assert.True(revokedKey1.IsRevoked);

        // Active key lookup should return key2
        var activeKey = await keyVaultService.GetActiveUserKeyAsync(userId);
        Assert.NotNull(activeKey);
        Assert.Equal(key2.Id, activeKey.Id);
    }

    [Fact]
    public async Task RegisterAsync_Automatically_Provisions_Rsa_Key_In_Database()
    {
        using var context = CreateInMemoryDbContext();
        var tokenService = new TokenService(_configuration);
        var keyVaultService = new KeyVaultService(context, _configuration);
        var authService = new AuthService(context, tokenService, keyVaultService);

        var (success, errorMessage, response) = await authService.RegisterAsync(new RegisterRequestDto
        {
            Username = "auto_rsa_user",
            Email = "rsa_user@test.com",
            Password = "Password123!"
        });

        Assert.True(success);
        Assert.NotNull(response);

        // Verify key was automatically created in database
        var key = await keyVaultService.GetActiveUserKeyAsync(response.UserId);
        Assert.NotNull(key);
        Assert.Equal(4096, key.KeySizeBits);
        Assert.StartsWith("-----BEGIN PUBLIC KEY-----", key.PublicKeyPem);

        // Verify User Profile indicates key existence
        var profile = await authService.GetUserProfileAsync(response.UserId);
        Assert.NotNull(profile);
        Assert.True(profile.HasRsaKey);
        Assert.Equal(4096, profile.ActiveKeySizeBits);
        Assert.NotNull(profile.KeyFingerprint);
    }
}
