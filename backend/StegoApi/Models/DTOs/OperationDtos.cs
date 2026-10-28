using System.ComponentModel.DataAnnotations;

namespace StegoApi.Models.DTOs;

public class RecordOperationRequestDto
{
    [Required]
    [MaxLength(50)]
    public string OperationType { get; set; } = "Encode"; // "Encode" or "Decode"

    [MaxLength(64)]
    public string CoverImageHash { get; set; } = string.Empty;

    [MaxLength(64)]
    public string StegoImageHash { get; set; } = string.Empty;

    public long PayloadSizeBytes { get; set; }

    [MaxLength(50)]
    public string SecurityLevel { get; set; } = "Balanced";

    public double? DetectabilityScore { get; set; }

    public double? PsnrDb { get; set; }

    public double? Ssim { get; set; }

    public double? Mse { get; set; }

    public long ExecutionTimeMs { get; set; }
}

public class OperationResponseDto
{
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public string OperationType { get; set; } = string.Empty;
    public string CoverImageHash { get; set; } = string.Empty;
    public string StegoImageHash { get; set; } = string.Empty;
    public long PayloadSizeBytes { get; set; }
    public string SecurityLevel { get; set; } = string.Empty;
    public double? DetectabilityScore { get; set; }
    public double? PsnrDb { get; set; }
    public double? Ssim { get; set; }
    public double? Mse { get; set; }
    public long ExecutionTimeMs { get; set; }
    public DateTime CreatedAt { get; set; }
}
