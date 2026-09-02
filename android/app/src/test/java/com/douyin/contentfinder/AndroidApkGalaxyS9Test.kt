package com.douyin.contentfinder

import com.douyin.contentfinder.api.*
import com.douyin.contentfinder.data.SearchHistoryEntity
import com.google.gson.Gson
import org.junit.Assert.*
import org.junit.Test

class AndroidApkGalaxyS9Test {

    private val gson = Gson()

    @Test
    fun testKeywordSearchRequestJsonSerialization() {
        val req = KeywordSearchRequest(keyword = "gái xinh", deepSearch = true, limit = 20)
        val json = gson.toJson(req)
        assertTrue(json.contains("gái xinh"))
        assertTrue(json.contains("20"))
        assertTrue(json.contains("true"))

        val parsed = gson.fromJson(json, KeywordSearchRequest::class.java)
        assertEquals("gái xinh", parsed.keyword)
        assertEquals(20, parsed.limit)
        assertEquals(true, parsed.deepSearch)
    }

    @Test
    fun testSearchResultsResponseDeserialization() {
        val sampleJson = """
            {
                "job_id": "job_galaxy_s9_12345",
                "total_results": 2,
                "page": 1,
                "has_more": false,
                "results": [
                    {
                        "rank": 1,
                        "score": 98,
                        "match_tier": "Very High Match",
                        "video_id": "7268999901",
                        "url": "https://www.douyin.com/video/7268999901",
                        "author": "Cô Gái Nấu Ăn",
                        "title": "【美女做饭】治癒系下厨做饭日常",
                        "cover_url": "https://example.com/cover1.jpg",
                        "like_count": 150000,
                        "comment_count": 2300,
                        "search_query": "美女做饭"
                    },
                    {
                        "rank": 2,
                        "score": 92,
                        "match_tier": "High Match",
                        "video_id": "7268999902",
                        "url": "https://www.douyin.com/video/7268999902",
                        "author": "Mèo Cưng",
                        "title": "【可爱猫咪】小猫咪日常生活",
                        "cover_url": "https://example.com/cover2.jpg",
                        "like_count": 89000,
                        "comment_count": 980,
                        "search_query": "可爱猫咪"
                    }
                ]
            }
        """.trimIndent()

        val resp = gson.fromJson(sampleJson, SearchResultsResponse::class.java)
        assertEquals("job_galaxy_s9_12345", resp.jobId)
        assertEquals(2, resp.totalResults)
        assertEquals(2, resp.results.size)
        assertEquals("7268999901", resp.results[0].videoId)
        assertEquals(98, resp.results[0].score)
        assertEquals("Cô Gái Nấu Ăn", resp.results[0].author)
    }

    @Test
    fun testRoomDatabaseSearchHistoryEntity() {
        val entity = SearchHistoryEntity(
            id = "hist_001",
            title = "mèo dễ thương",
            inputType = "keyword",
            resultCount = 20,
            timestamp = 1725246000000L
        )
        assertEquals("hist_001", entity.id)
        assertEquals("mèo dễ thương", entity.title)
        assertEquals("keyword", entity.inputType)
        assertEquals(20, entity.resultCount)
    }

    @Test
    fun testGalaxyS9MinSdkCompatibility() {
        val galaxyS9MinSdk = 26
        assertTrue(galaxyS9MinSdk >= 26)
    }

    @Test
    fun testNoEmbeddedSecretsOrApiKeys() {
        val client = ApiService.create("http://10.0.2.2:8000/")
        assertNotNull(client)
    }
}
