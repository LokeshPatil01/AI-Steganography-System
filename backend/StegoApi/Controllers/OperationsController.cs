using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using StegoApi.Data;
using StegoApi.Models.DTOs;
using StegoApi.Models.Entities;

namespace StegoApi.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class OperationsController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public OperationsController(ApplicationDbContext context)
    {
        _context = context;
    }

    /// <summary>
    /// Retrieves the authenticated user's steganographic operation history.
    /// </summary>
    [HttpGet("history")]
    public async Task<IActionResult> GetOperationHistory([FromQuery] int limit = 50)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(new { message = "Invalid token credentials." });

        var operations = await _context.StegoOperations
            .Where(o => o.UserId == userId.Value)
            .OrderByDescending(o => o.CreatedAt)
            .Take(Math.Min(limit, 100))
            .Select(o => new OperationResponseDto
            {
                Id = o.Id,
                UserId = o.UserId,
                OperationType = o.OperationType,
                CoverImageHash = o.CoverImageHash,
                StegoImageHash = o.StegoImageHash,
                PayloadSizeBytes = o.PayloadSizeBytes,
                SecurityLevel = o.SecurityLevel,
                DetectabilityScore = o.DetectabilityScore,
                PsnrDb = o.PsnrDb,
                Ssim = o.Ssim,
                Mse = o.Mse,
                ExecutionTimeMs = o.ExecutionTimeMs,
                CreatedAt = o.CreatedAt
            })
            .ToListAsync();

        return Ok(operations);
    }

    /// <summary>
    /// Records a completed steganographic operation for forensics and auditing.
    /// </summary>
    [HttpPost("audit")]
    public async Task<IActionResult> RecordOperation([FromBody] RecordOperationRequestDto request)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(new { message = "Invalid token credentials." });

        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        var operation = new StegoOperation
        {
            UserId = userId.Value,
            OperationType = request.OperationType,
            CoverImageHash = request.CoverImageHash ?? string.Empty,
            StegoImageHash = request.StegoImageHash ?? string.Empty,
            PayloadSizeBytes = request.PayloadSizeBytes,
            SecurityLevel = request.SecurityLevel ?? "Balanced",
            DetectabilityScore = request.DetectabilityScore,
            PsnrDb = request.PsnrDb,
            Ssim = request.Ssim,
            Mse = request.Mse,
            ExecutionTimeMs = request.ExecutionTimeMs,
            CreatedAt = DateTime.UtcNow
        };

        _context.StegoOperations.Add(operation);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetOperationById), new { id = operation.Id }, new OperationResponseDto
        {
            Id = operation.Id,
            UserId = operation.UserId,
            OperationType = operation.OperationType,
            CoverImageHash = operation.CoverImageHash,
            StegoImageHash = operation.StegoImageHash,
            PayloadSizeBytes = operation.PayloadSizeBytes,
            SecurityLevel = operation.SecurityLevel,
            DetectabilityScore = operation.DetectabilityScore,
            PsnrDb = operation.PsnrDb,
            Ssim = operation.Ssim,
            Mse = operation.Mse,
            ExecutionTimeMs = operation.ExecutionTimeMs,
            CreatedAt = operation.CreatedAt
        });
    }

    /// <summary>
    /// Retrieves details of a specific steganographic operation by ID.
    /// </summary>
    [HttpGet("{id:guid}")]
    public async Task<IActionResult> GetOperationById(Guid id)
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(new { message = "Invalid token credentials." });

        var operation = await _context.StegoOperations
            .FirstOrDefaultAsync(o => o.Id == id && o.UserId == userId.Value);

        if (operation == null)
            return NotFound(new { message = "Operation record not found." });

        return Ok(new OperationResponseDto
        {
            Id = operation.Id,
            UserId = operation.UserId,
            OperationType = operation.OperationType,
            CoverImageHash = operation.CoverImageHash,
            StegoImageHash = operation.StegoImageHash,
            PayloadSizeBytes = operation.PayloadSizeBytes,
            SecurityLevel = operation.SecurityLevel,
            DetectabilityScore = operation.DetectabilityScore,
            PsnrDb = operation.PsnrDb,
            Ssim = operation.Ssim,
            Mse = operation.Mse,
            ExecutionTimeMs = operation.ExecutionTimeMs,
            CreatedAt = operation.CreatedAt
        });
    }

    private Guid? GetCurrentUserId()
    {
        var claim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (Guid.TryParse(claim, out var id))
            return id;
        return null;
    }
}
