using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using StegoApi.Models.DTOs;
using Xunit;

namespace StegoApi.Tests;

public class KeysControllerIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public KeysControllerIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
    }

    [Fact]
    public async Task Keys_Endpoints_Retrieve_And_Regenerate_Rsa_Keys_Successfully()
    {
        var client = _factory.CreateClient();

        // 1. Register User A
        string suffixA = Guid.NewGuid().ToString("N")[..8];
        var regA = new RegisterRequestDto
        {
            Username = $"userA_{suffixA}",
            Email = $"userA_{suffixA}@crypto.edu",
            Password = "PasswordA123!"
        };
        var regRespA = await client.PostAsJsonAsync("/api/auth/register", regA);
        Assert.Equal(HttpStatusCode.Created, regRespA.StatusCode);
        var authDataA = await regRespA.Content.ReadFromJsonAsync<AuthResponseDto>();
        Assert.NotNull(authDataA);

        // 2. Register User B (recipient)
        string suffixB = Guid.NewGuid().ToString("N")[..8];
        var regB = new RegisterRequestDto
        {
            Username = $"userB_{suffixB}",
            Email = $"userB_{suffixB}@crypto.edu",
            Password = "PasswordB123!"
        };
        var regRespB = await client.PostAsJsonAsync("/api/auth/register", regB);
        Assert.Equal(HttpStatusCode.Created, regRespB.StatusCode);
        var authDataB = await regRespB.Content.ReadFromJsonAsync<AuthResponseDto>();
        Assert.NotNull(authDataB);

        // 3. User A retrieves their own public key
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", authDataA.Token);
        var myKeyResp = await client.GetAsync("/api/keys/public-key");
        Assert.Equal(HttpStatusCode.OK, myKeyResp.StatusCode);

        var myKeyData = await myKeyResp.Content.ReadFromJsonAsync<PublicKeyResponseDto>();
        Assert.NotNull(myKeyData);
        Assert.Equal(authDataA.UserId, myKeyData.UserId);
        Assert.Equal(4096, myKeyData.KeySizeBits);
        Assert.StartsWith("-----BEGIN PUBLIC KEY-----", myKeyData.PublicKeyPem);
        Assert.StartsWith("SHA256:", myKeyData.KeyFingerprint);

        // 4. User A retrieves User B's public key (recipient public key lookup)
        var recipientKeyResp = await client.GetAsync($"/api/keys/user/{authDataB.UserId}/public-key");
        Assert.Equal(HttpStatusCode.OK, recipientKeyResp.StatusCode);

        var recipientKeyData = await recipientKeyResp.Content.ReadFromJsonAsync<PublicKeyResponseDto>();
        Assert.NotNull(recipientKeyData);
        Assert.Equal(authDataB.UserId, recipientKeyData.UserId);
        Assert.StartsWith("-----BEGIN PUBLIC KEY-----", recipientKeyData.PublicKeyPem);

        // 5. User A regenerates keys
        var regenResp = await client.PostAsync("/api/keys/regenerate", null);
        Assert.Equal(HttpStatusCode.OK, regenResp.StatusCode);

        var regenData = await regenResp.Content.ReadFromJsonAsync<KeyRegenerationResponseDto>();
        Assert.NotNull(regenData);
        Assert.Equal(authDataA.UserId, regenData.UserId);
        Assert.NotEqual(myKeyData.KeyFingerprint, regenData.KeyFingerprint); // Fresh key generated
    }
}
