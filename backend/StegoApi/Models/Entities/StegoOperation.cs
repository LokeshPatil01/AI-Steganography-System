using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace StegoApi.Models.Entities;

[Table("StegoOperations")]
public class StegoOperation
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    [Required]
    public Guid UserId { get; set; }

    [ForeignKey(nameof(UserId))]
    public virtual User? User { get; set; }

    [Required]
    [MaxLength(50)]
    public string OperationType { get; set; } = "Encode"; // "Encode" or "Decode"

    [MaxLength(64)]
    public string CoverImageHash { get; set; } = string.Empty;

    [MaxLength(64)]
    public string StegoImageHash { get; set; } = string.Empty;

    public long PayloadSizeBytes { get; set; }

    [MaxLength(50)]
    public string SecurityLevel { get; set; } = "Balanced"; // "Quality", "Balanced", "Security"

    public double? DetectabilityScore { get; set; } // CNN Steganalyzer P(stego)

    public double? PsnrDb { get; set; }

    public double? Ssim { get; set; }

    public double? Mse { get; set; }

    public long ExecutionTimeMs { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
