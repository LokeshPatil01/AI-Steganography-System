using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using StegoApi.Models.DTOs;
using Xunit;
using Xunit.Abstractions;

namespace StegoApi.Tests;

public class AuthIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;
    private readonly ITestOutputHelper _output;

    public AuthIntegrationTests(WebApplicationFactory<Program> factory, ITestOutputHelper output)
    {
        _factory = factory;
        _output = output;
    }

    [Fact]
    public async Task Complete_Auth_Lifecycle_Register_Login_GetProfile_Works_Over_Http()
    {
        var client = _factory.CreateClient();

        // 1. Register a new user with unique email
        string uniqueSuffix = Guid.NewGuid().ToString("N")[..8];
        var registerRequest = new RegisterRequestDto
        {
            Username = $"user_{uniqueSuffix}",
            Email = $"user_{uniqueSuffix}@university.edu",
            Password = "SecurePassword123!"
        };

        var regResponse = await client.PostAsJsonAsync("/api/auth/register", registerRequest);
        var regBody = await regResponse.Content.ReadAsStringAsync();
        _output.WriteLine($"Register Response: {regResponse.StatusCode} -> {regBody}");

        Assert.True(regResponse.IsSuccessStatusCode, $"Register failed with: {regResponse.StatusCode} - {regBody}");
        Assert.Equal(HttpStatusCode.Created, regResponse.StatusCode);

        var regData = await regResponse.Content.ReadFromJsonAsync<AuthResponseDto>();
        Assert.NotNull(regData);
        Assert.Equal(registerRequest.Username, regData.Username);
        Assert.False(string.IsNullOrEmpty(regData.Token));

        // 2. Login with registered credentials
        var loginRequest = new LoginRequestDto
        {
            Email = registerRequest.Email,
            Password = "SecurePassword123!"
        };

        var loginResponse = await client.PostAsJsonAsync("/api/auth/login", loginRequest);
        Assert.Equal(HttpStatusCode.OK, loginResponse.StatusCode);

        var loginData = await loginResponse.Content.ReadFromJsonAsync<AuthResponseDto>();
        Assert.NotNull(loginData);
        Assert.Equal(registerRequest.Username, loginData.Username);
        Assert.False(string.IsNullOrEmpty(loginData.Token));

        // 3. Request profile WITHOUT token -> Expect 401 Unauthorized
        var unauthResponse = await client.GetAsync("/api/auth/profile");
        Assert.Equal(HttpStatusCode.Unauthorized, unauthResponse.StatusCode);

        // 4. Request profile WITH Bearer token -> Expect 200 OK
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", loginData.Token);
        var profileResponse = await client.GetAsync("/api/auth/profile");
        Assert.Equal(HttpStatusCode.OK, profileResponse.StatusCode);

        var profileData = await profileResponse.Content.ReadFromJsonAsync<UserProfileDto>();
        Assert.NotNull(profileData);
        Assert.Equal(registerRequest.Username, profileData.Username);
        Assert.Equal(registerRequest.Email, profileData.Email);
    }
}
