namespace StegoApi.Models.DTOs;

public class PublicKeyResponseDto
{
    public Guid UserId { get; set; }
    public string PublicKeyPem { get; set; } = string.Empty;
    public string KeyFingerprint { get; set; } = string.Empty;
    public int KeySizeBits { get; set; } = 4096;
    public DateTime CreatedAt { get; set; }
}

public class KeyRegenerationResponseDto
{
    public string Message { get; set; } = string.Empty;
    public Guid UserId { get; set; }
    public string PublicKeyPem { get; set; } = string.Empty;
    public string KeyFingerprint { get; set; } = string.Empty;
    public int KeySizeBits { get; set; } = 4096;
    public DateTime CreatedAt { get; set; }
}
