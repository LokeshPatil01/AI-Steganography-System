using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using StegoApi.Models.DTOs;
using Xunit;

namespace StegoApi.Tests;

public class OperationsControllerIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public OperationsControllerIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
    }

    [Fact]
    public async Task Operations_Audit_And_History_Cycle_Succeeds()
    {
        var client = _factory.CreateClient();

        // 1. Register User
        string suffix = Guid.NewGuid().ToString("N")[..8];
        var reg = new RegisterRequestDto
        {
            Username = $"opuser_{suffix}",
            Email = $"opuser_{suffix}@stego.edu",
            Password = "PasswordOp123!"
        };
        var regResp = await client.PostAsJsonAsync("/api/auth/register", reg);
        Assert.Equal(HttpStatusCode.Created, regResp.StatusCode);
        var authData = await regResp.Content.ReadFromJsonAsync<AuthResponseDto>();
        Assert.NotNull(authData);

        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", authData.Token);

        // 2. Audit new operation
        var opDto = new RecordOperationRequestDto
        {
            OperationType = "Encode",
            CoverImageHash = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            StegoImageHash = "f9e8d7c6b5a43210f9e8d7c6b5a43210f9e8d7c6b5a43210f9e8d7c6b5a43210",
            PayloadSizeBytes = 1024,
            SecurityLevel = "Balanced",
            DetectabilityScore = 0.082,
            PsnrDb = 42.45,
            Ssim = 0.9921,
            Mse = 0.0034,
            ExecutionTimeMs = 145
        };

        var auditResp = await client.PostAsJsonAsync("/api/operations/audit", opDto);
        Assert.Equal(HttpStatusCode.Created, auditResp.StatusCode);
        var createdOp = await auditResp.Content.ReadFromJsonAsync<OperationResponseDto>();
        Assert.NotNull(createdOp);
        Assert.Equal(authData.UserId, createdOp.UserId);
        Assert.Equal("Encode", createdOp.OperationType);
        Assert.Equal(42.45, createdOp.PsnrDb);
        Assert.Equal(0.082, createdOp.DetectabilityScore);

        // 3. Query history
        var histResp = await client.GetAsync("/api/operations/history");
        Assert.Equal(HttpStatusCode.OK, histResp.StatusCode);
        var history = await histResp.Content.ReadFromJsonAsync<List<OperationResponseDto>>();
        Assert.NotNull(history);
        Assert.NotEmpty(history);
        Assert.Contains(history, o => o.Id == createdOp.Id);

        // 4. Query by ID
        var byIdResp = await client.GetAsync($"/api/operations/{createdOp.Id}");
        Assert.Equal(HttpStatusCode.OK, byIdResp.StatusCode);
        var fetchedOp = await byIdResp.Content.ReadFromJsonAsync<OperationResponseDto>();
        Assert.NotNull(fetchedOp);
        Assert.Equal(createdOp.Id, fetchedOp.Id);
    }
}
