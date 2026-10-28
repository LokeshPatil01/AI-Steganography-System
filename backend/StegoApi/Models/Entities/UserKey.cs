using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace StegoApi.Models.Entities;

[Table("UserKeys")]
public class UserKey
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    [Required]
    public Guid UserId { get; set; }

    [ForeignKey(nameof(UserId))]
    public virtual User? User { get; set; }

    [Required]
    public string PublicKeyPem { get; set; } = string.Empty;

    /// <summary>
    /// AES-256-GCM encrypted PKCS#8 RSA private key.
    /// NEVER stored in plaintext.
    /// </summary>
    [Required]
    public string EncryptedPrivateKeyPem { get; set; } = string.Empty;

    /// <summary>
    /// 96-bit initialization vector used for GCM encryption of private key (Base64 encoded).
    /// </summary>
    [Required]
    [MaxLength(64)]
    public string KeyIv { get; set; } = string.Empty;

    /// <summary>
    /// 128-bit authentication tag validating private key cipher integrity (Base64 encoded).
    /// </summary>
    [Required]
    [MaxLength(64)]
    public string KeyTag { get; set; } = string.Empty;

    /// <summary>
    /// SHA-256 digest of the public key for fast fingerprint lookup (e.g. SHA256:HEX).
    /// </summary>
    [Required]
    [MaxLength(128)]
    public string KeyFingerprint { get; set; } = string.Empty;

    public int KeySizeBits { get; set; } = 4096;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public bool IsRevoked { get; set; } = false;
}
