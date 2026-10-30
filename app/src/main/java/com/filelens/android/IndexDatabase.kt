package com.filelens.android

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

data class SearchHit(val uri: String, val page: Int, val snippet: String)

class IndexDatabase(context: Context) : SQLiteOpenHelper(context, "filelens_android.db", null, 1) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""CREATE VIRTUAL TABLE pages USING fts4(
            uri UNINDEXED, page UNINDEXED, text, tokenize=unicode61
        )""")
    }
    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit

    fun replaceDocument(uri: String, pages: List<Pair<Int, String>>) {
        val db = writableDatabase
        db.beginTransaction()
        try {
            db.delete("pages", "uri = ?", arrayOf(uri))
            pages.forEach { (number, text) ->
                val values = ContentValues().apply {
                    put("uri", uri); put("page", number); put("text", text)
                }
                db.insertOrThrow("pages", null, values)
            }
            db.setTransactionSuccessful()
        } finally { db.endTransaction() }
    }

    fun search(input: String): List<SearchHit> {
        val terms = input.trim().split(Regex("\\s+")).filter { it.isNotBlank() }
        if (terms.isEmpty()) return emptyList()
        val match = terms.joinToString(" AND ") { "\"" + it.replace("\"", "\"\"") + "\"" }
        val hits = mutableListOf<SearchHit>()
        readableDatabase.rawQuery(
            "SELECT uri, page, snippet(pages, 2, '[', ']', '…', 12) " +
                "FROM pages WHERE pages MATCH ? LIMIT 100", arrayOf(match)
        ).use { cursor ->
            while (cursor.moveToNext()) hits += SearchHit(
                cursor.getString(0), cursor.getInt(1), cursor.getString(2)
            )
        }
        return hits
    }

    fun indexedPageCount(): Int = readableDatabase.rawQuery("SELECT COUNT(*) FROM pages", null).use {
        if (it.moveToFirst()) it.getInt(0) else 0
    }
}
