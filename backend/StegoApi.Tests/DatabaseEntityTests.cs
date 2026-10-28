using Microsoft.EntityFrameworkCore;
using StegoApi.Data;
using StegoApi.Models.Entities;
using Xunit;

namespace StegoApi.Tests;

public class DatabaseEntityTests
{
    private ApplicationDbContext CreateInMemoryDbContext()
    {
        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        return new ApplicationDbContext(options);
    }

    [Fact]
    public async Task Can_Add_User_With_UserKey_And_StegoOperation()
    {
        using var context = CreateInMemoryDbContext();

        var user = new User
        {
            Username = "researcher1",
            Email = "researcher@university.edu",
            PasswordHash = "hashed_pw_example",
            PasswordSalt = "salt_example_128bit",
            CreatedAt = DateTime.UtcNow,
            IsActive = true
        };

        var key = new UserKey
        {
            UserId = user.Id,
            User = user,
            PublicKeyPem = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...\n-----END PUBLIC KEY-----",
            EncryptedPrivateKeyPem = "ENC:GCM:48593457893457...",
            KeyIv = "kIvRandom96Bit==",
            KeyTag = "kTagAuth128Bit==",
            KeyFingerprint = "a1b2c3d4e5f67890abcdef1234567890",
            KeySizeBits = 4096,
            CreatedAt = DateTime.UtcNow,
            IsRevoked = false
        };

        var operation = new StegoOperation
        {
            UserId = user.Id,
            User = user,
            OperationType = "Encode",
            CoverImageHash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            StegoImageHash = "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
            PayloadSizeBytes = 2048,
            SecurityLevel = "Balanced",
            DetectabilityScore = 0.12,
            PsnrDb = 48.5,
            Ssim = 0.992,
            Mse = 0.85,
            ExecutionTimeMs = 125,
            CreatedAt = DateTime.UtcNow
        };

        user.Keys.Add(key);
        user.Operations.Add(operation);

        context.Users.Add(user);
        await context.SaveChangesAsync();

        // Query back from DB
        var savedUser = await context.Users
            .Include(u => u.Keys)
            .Include(u => u.Operations)
            .FirstOrDefaultAsync(u => u.Email == "researcher@university.edu");

        Assert.NotNull(savedUser);
        Assert.Equal("researcher1", savedUser.Username);
        Assert.Single(savedUser.Keys);
        Assert.Single(savedUser.Operations);

        var savedKey = savedUser.Keys.First();
        Assert.Equal(4096, savedKey.KeySizeBits);
        Assert.False(savedKey.IsRevoked);
        Assert.False(string.IsNullOrEmpty(savedKey.EncryptedPrivateKeyPem));
        Assert.False(string.IsNullOrEmpty(savedKey.KeyTag));

        var savedOp = savedUser.Operations.First();
        Assert.Equal("Encode", savedOp.OperationType);
        Assert.Equal(48.5, savedOp.PsnrDb);
    }

    [Fact]
    public async Task Cascade_Delete_Removes_Associated_Keys_And_Operations()
    {
        using var context = CreateInMemoryDbContext();

        var user = new User
        {
            Username = "temp_user",
            Email = "temp@example.com",
            PasswordHash = "hash",
            PasswordSalt = "salt"
        };

        var key = new UserKey
        {
            UserId = user.Id,
            PublicKeyPem = "pub",
            EncryptedPrivateKeyPem = "enc_priv",
            KeyIv = "iv",
            KeyTag = "tag",
            KeyFingerprint = "fp"
        };

        context.Users.Add(user);
        context.UserKeys.Add(key);
        await context.SaveChangesAsync();

        // Verify inserted
        Assert.Equal(1, await context.Users.CountAsync());
        Assert.Equal(1, await context.UserKeys.CountAsync());

        // Delete user
        context.Users.Remove(user);
        await context.SaveChangesAsync();

        // Cascade delete should clear UserKeys
        Assert.Equal(0, await context.Users.CountAsync());
        Assert.Equal(0, await context.UserKeys.CountAsync());
    }
}
