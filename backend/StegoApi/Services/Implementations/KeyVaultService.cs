using System.Security.Cryptography;
using System.Text;
using Microsoft.EntityFrameworkCore;
using StegoApi.Data;
using StegoApi.Models.Entities;
using StegoApi.Services.Interfaces;

namespace StegoApi.Services.Implementations;

public class KeyVaultService : IKeyVaultService
{
    private const int RsaKeySizeBits = 4096;
    private const int GcmNonceSizeBytes = 12; // 96-bit recommended for GCM
    private const int GcmTagSizeBytes = 16;   // 128-bit authentication tag
    private const int KekSizeBytes = 32;       // 256-bit AES key

    private readonly ApplicationDbContext _context;
    private readonly IConfiguration _configuration;

    public KeyVaultService(ApplicationDbContext context, IConfiguration configuration)
    {
        _context = context;
        _configuration = configuration;
    }

    public async Task<UserKey> GenerateAndStoreUserKeyAsync(Guid userId, string userPasswordHash)
    {
        // 1. Generate fresh 4096-bit RSA key pair
        using var rsa = RSA.Create(RsaKeySizeBits);

        string publicKeyPem = rsa.ExportSubjectPublicKeyInfoPem();
        string privateKeyPem = rsa.ExportPkcs8PrivateKeyPem();

        // 2. Compute public key SHA-256 fingerprint
        byte[] pubDer = rsa.ExportSubjectPublicKeyInfo();
        byte[] hash = SHA256.HashData(pubDer);
        string fingerprint = "SHA256:" + Convert.ToHexString(hash);

        // 3. Derive Key Encryption Key (KEK) using HKDF-SHA256
        byte[] kek = DeriveKek(userId, userPasswordHash);

        // 4. Encrypt private key using authenticated AES-256-GCM
        byte[] iv = RandomNumberGenerator.GetBytes(GcmNonceSizeBytes);
        byte[] plaintextBytes = Encoding.UTF8.GetBytes(privateKeyPem);
        byte[] ciphertext = new byte[plaintextBytes.Length];
        byte[] tag = new byte[GcmTagSizeBytes];

        using (var aesGcm = new AesGcm(kek, GcmTagSizeBytes))
        {
            aesGcm.Encrypt(iv, plaintextBytes, ciphertext, tag);
        }

        // 5. Zero out plaintext in memory
        CryptographicOperations.ZeroMemory(plaintextBytes);
        CryptographicOperations.ZeroMemory(kek);

        // 6. Save encrypted key vault entity
        var userKey = new UserKey
        {
            Id = Guid.NewGuid(),
            UserId = userId,
            PublicKeyPem = publicKeyPem,
            EncryptedPrivateKeyPem = Convert.ToBase64String(ciphertext),
            KeyIv = Convert.ToBase64String(iv),
            KeyTag = Convert.ToBase64String(tag),
            KeyFingerprint = fingerprint,
            KeySizeBits = RsaKeySizeBits,
            CreatedAt = DateTime.UtcNow,
            IsRevoked = false
        };

        _context.UserKeys.Add(userKey);
        await _context.SaveChangesAsync();

        return userKey;
    }

    public async Task<UserKey?> GetActiveUserKeyAsync(Guid userId)
    {
        return await _context.UserKeys
            .Where(k => k.UserId == userId && !k.IsRevoked)
            .OrderByDescending(k => k.CreatedAt)
            .FirstOrDefaultAsync();
    }

    public async Task<string?> DecryptUserPrivateKeyPemAsync(Guid userId, string userPasswordHash)
    {
        var keyRecord = await GetActiveUserKeyAsync(userId);
        if (keyRecord == null)
            return null;

        try
        {
            byte[] kek = DeriveKek(userId, userPasswordHash);
            byte[] iv = Convert.FromBase64String(keyRecord.KeyIv);
            byte[] tag = Convert.FromBase64String(keyRecord.KeyTag);
            byte[] ciphertext = Convert.FromBase64String(keyRecord.EncryptedPrivateKeyPem);
            byte[] decryptedBytes = new byte[ciphertext.Length];

            using (var aesGcm = new AesGcm(kek, GcmTagSizeBytes))
            {
                aesGcm.Decrypt(iv, ciphertext, tag, decryptedBytes);
            }

            CryptographicOperations.ZeroMemory(kek);
            string privateKeyPem = Encoding.UTF8.GetString(decryptedBytes);
            CryptographicOperations.ZeroMemory(decryptedBytes);

            return privateKeyPem;
        }
        catch (CryptographicException)
        {
            // Tag mismatch or corrupted key data
            return null;
        }
    }

    public async Task<UserKey> RegenerateUserKeyAsync(Guid userId, string userPasswordHash)
    {
        // Revoke any previous active keys
        var existingKeys = await _context.UserKeys
            .Where(k => k.UserId == userId && !k.IsRevoked)
            .ToListAsync();

        foreach (var key in existingKeys)
        {
            key.IsRevoked = true;
        }

        // Generate and store new key pair
        return await GenerateAndStoreUserKeyAsync(userId, userPasswordHash);
    }

    /// <summary>
    /// Derives a 256-bit Key Encryption Key (KEK) using HKDF-SHA256 from user's password hash and system master key.
    /// </summary>
    private byte[] DeriveKek(Guid userId, string userPasswordHash)
    {
        string systemSecret = _configuration["JwtSettings:Secret"]
            ?? "FallbackMasterSystemVaultKeyForSteganography2026!";

        byte[] ikm = Encoding.UTF8.GetBytes(userPasswordHash);
        byte[] salt = Encoding.UTF8.GetBytes(systemSecret);
        byte[] info = Encoding.UTF8.GetBytes($"StegoKeyVaultKEK:{userId:N}");

        return HKDF.DeriveKey(HashAlgorithmName.SHA256, ikm, KekSizeBytes, salt, info);
    }
}
