<?php

/// Posted on @TheSmartDev || @ISmartDevs
/// Developer @ISmartDevs
header("Content-Type: application/json; charset=UTF-8");

if (!isset($_GET['url']) || empty($_GET['url'])) {
    echo json_encode([
        "error" => "Hey Bro Kindly Give URL",
        "dev" => "@ISmartDevs",
        "channel" => "@TheSmartDev"
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

$facebook_video_url = $_GET['url'];
$encoded_url = urlencode($facebook_video_url);
$api_url = "https://tooly.chative.io/facebook/video?url=" . $encoded_url;

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $api_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
$response = curl_exec($ch);
if (curl_errno($ch)) {
    echo json_encode([
        "error" => "cURL error: " . curl_error($ch),
        "dev" => "@ISmartDevs",
        "channel" => "@TheSmartDev"
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    curl_close($ch);
    exit;
}
curl_close($ch);
$data = json_decode($response, true);

if ($data && isset($data["success"]) && $data["success"] === true) {
    $title = $data["title"] ?? "No Title";
    $sd_url = $data["videos"]["sd"]["url"];
    $hd_url = $data["videos"]["hd"]["url"];
    $result = [
        "success" => true,
        "title" => $title,
        "sd_url" => $sd_url,
        "hd_url" => $hd_url,
        "dev" => "@ISmartDevs",
        "channel" => "@TheSmartDev"
    ];
} else {
    $result = [
        "success" => false,
        "error" => $data["message"] ?? "Unknown error",
        "dev" => "@ISmartDevs",
        "channel" => "@TheSmartDev"
    ];
}

echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);

?>
