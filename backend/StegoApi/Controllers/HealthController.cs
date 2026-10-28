using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using StegoApi.Data;

namespace StegoApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class HealthController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public HealthController(ApplicationDbContext context)
    {
        _context = context;
    }

    [HttpGet]
    public async Task<IActionResult> GetHealth()
    {
        bool dbConnected = false;
        string dbError = string.Empty;

        try
        {
            dbConnected = await _context.Database.CanConnectAsync();
        }
        catch (Exception ex)
        {
            dbError = ex.Message;
        }

        return Ok(new
        {
            status = dbConnected ? "healthy" : "degraded",
            service = "StegoApi",
            version = "1.0.0",
            framework = ".NET 10.0",
            database = new
            {
                provider = "Microsoft SQL Server",
                connected = dbConnected,
                error = string.IsNullOrEmpty(dbError) ? null : dbError
            },
            timestamp = DateTime.UtcNow
        });
    }
}
