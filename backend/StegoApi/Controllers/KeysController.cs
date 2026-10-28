using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using StegoApi.Data;
using StegoApi.Models.DTOs;
using StegoApi.Services.Interfaces;

namespace StegoApi.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class KeysController : ControllerBase
{
    private readonly IKeyVaultService _keyVaultService;
    private readonly ApplicationDbContext _context;

    public KeysController(IKeyVaultService keyVaultService, ApplicationDbContext context)
    {
        _keyVaultService = keyVaultService;
        _context = context;
    }

    /// <summary>
    /// Retrieves the authenticated user's active RSA Public Key in PEM format.
    /// </summary>
    [HttpGet("public-key")]
    public async Task<IActionResult> GetMyPublicKey()
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(new { message = "Invalid token credentials." });

        var key = await _keyVaultService.GetActiveUserKeyAsync(userId.Value);
        if (key == null)
            return NotFound(new { message = "No active cryptographic key found for user." });

        return Ok(new PublicKeyResponseDto
        {
            UserId = key.UserId,
            PublicKeyPem = key.PublicKeyPem,
            KeyFingerprint = key.KeyFingerprint,
            KeySizeBits = key.KeySizeBits,
            CreatedAt = key.CreatedAt
        });
    }

    /// <summary>
    /// Retrieves the authenticated user's active RSA Private Key in PEM format.
    /// Decrypted in memory using authenticated user credentials.
    /// </summary>
    [HttpGet("private-key")]
    public async Task<IActionResult> GetMyPrivateKey()
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(new { message = "Invalid token credentials." });

        var user = await _context.Users.FindAsync(userId.Value);
        if (user == null)
            return NotFound(new { message = "User not found." });

        var privateKeyPem = await _keyVaultService.DecryptUserPrivateKeyPemAsync(user.Id, user.PasswordHash);
        if (string.IsNullOrEmpty(privateKeyPem))
            return NotFound(new { message = "Private key not found or decryption failed." });

        return Ok(new
        {
            userId = user.Id,
            privateKeyPem = privateKeyPem
        });
    }

    /// <summary>
    /// Retrieves the public key of any designated recipient user for message encryption.
    /// </summary>
    [HttpGet("user/{targetUserId:guid}/public-key")]
    public async Task<IActionResult> GetRecipientPublicKey(Guid targetUserId)
    {
        var key = await _keyVaultService.GetActiveUserKeyAsync(targetUserId);
        if (key == null)
            return NotFound(new { message = "Recipient does not have an active public key." });

        return Ok(new PublicKeyResponseDto
        {
            UserId = key.UserId,
            PublicKeyPem = key.PublicKeyPem,
            KeyFingerprint = key.KeyFingerprint,
            KeySizeBits = key.KeySizeBits,
            CreatedAt = key.CreatedAt
        });
    }

    /// <summary>
    /// Regenerates and rotates the user's RSA-4096 key pair.
    /// Revokes previous key while preserving legacy records.
    /// </summary>
    [HttpPost("regenerate")]
    public async Task<IActionResult> RegenerateKeys()
    {
        var userId = GetCurrentUserId();
        if (userId == null)
            return Unauthorized(new { message = "Invalid token credentials." });

        var user = await _context.Users.FindAsync(userId.Value);
        if (user == null)
            return NotFound(new { message = "User not found." });

        var newKey = await _keyVaultService.RegenerateUserKeyAsync(user.Id, user.PasswordHash);

        return Ok(new KeyRegenerationResponseDto
        {
            Message = "RSA-4096 key pair regenerated successfully. Previous key revoked.",
            UserId = newKey.UserId,
            PublicKeyPem = newKey.PublicKeyPem,
            KeyFingerprint = newKey.KeyFingerprint,
            KeySizeBits = newKey.KeySizeBits,
            CreatedAt = newKey.CreatedAt
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
