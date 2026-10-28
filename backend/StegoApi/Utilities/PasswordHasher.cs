using System.Security.Cryptography;

namespace StegoApi.Utilities;

public static class PasswordHasher
{
    private const int SaltSizeBytes = 16; // 128-bit salt
    private const int HashSizeBytes = 32; // 256-bit hash
    private const int Iterations = 100_000; // OWASP recommended PBKDF2 iterations

    /// <summary>
    /// Generates a cryptographically secure random salt and computes a PBKDF2-HMAC-SHA256 hash.
    /// </summary>
    public static (string Hash, string Salt) HashPassword(string password)
    {
        if (string.IsNullOrWhiteSpace(password))
            throw new ArgumentException("Password cannot be null or empty.", nameof(password));

        byte[] saltBytes = RandomNumberGenerator.GetBytes(SaltSizeBytes);
        byte[] hashBytes = Rfc2898DeriveBytes.Pbkdf2(
            password: password,
            salt: saltBytes,
            iterations: Iterations,
            hashAlgorithm: HashAlgorithmName.SHA256,
            outputLength: HashSizeBytes);

        return (Convert.ToBase64String(hashBytes), Convert.ToBase64String(saltBytes));
    }

    /// <summary>
    /// Verifies a password against the stored hash and salt using constant-time comparison.
    /// </summary>
    public static bool VerifyPassword(string password, string storedHashBase64, string storedSaltBase64)
    {
        if (string.IsNullOrWhiteSpace(password) ||
            string.IsNullOrWhiteSpace(storedHashBase64) ||
            string.IsNullOrWhiteSpace(storedSaltBase64))
        {
            return false;
        }

        try
        {
            byte[] saltBytes = Convert.FromBase64String(storedSaltBase64);
            byte[] expectedHashBytes = Convert.FromBase64String(storedHashBase64);

            byte[] actualHashBytes = Rfc2898DeriveBytes.Pbkdf2(
                password: password,
                salt: saltBytes,
                iterations: Iterations,
                hashAlgorithm: HashAlgorithmName.SHA256,
                outputLength: HashSizeBytes);

            // Constant-time comparison prevents timing side-channel attacks
            return CryptographicOperations.FixedTimeEquals(actualHashBytes, expectedHashBytes);
        }
        catch
        {
            return false;
        }
    }
}
