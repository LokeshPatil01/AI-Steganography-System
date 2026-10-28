using StegoApi.Models.Entities;

namespace StegoApi.Services.Interfaces;

public interface IKeyVaultService
{
    /// <summary>
    /// Generates a new 4096-bit RSA key pair, encrypts the private key with AES-256-GCM,
    /// and saves it to the database.
    /// </summary>
    Task<UserKey> GenerateAndStoreUserKeyAsync(Guid userId, string userPasswordHash);

    /// <summary>
    /// Retrieves the active public key in PEM format for a specified user.
    /// </summary>
    Task<UserKey?> GetActiveUserKeyAsync(Guid userId);

    /// <summary>
    /// Decrypts the active private key in volatile memory using user credentials.
    /// NEVER writes decrypted key to disk or transmits across public network.
    /// </summary>
    Task<string?> DecryptUserPrivateKeyPemAsync(Guid userId, string userPasswordHash);

    /// <summary>
    /// Revokes current keys and generates a fresh 4096-bit RSA key pair.
    /// </summary>
    Task<UserKey> RegenerateUserKeyAsync(Guid userId, string userPasswordHash);
}
