package com.filelens.android

import android.content.Context
import android.net.Uri
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper

object PdfIndexer {
    fun index(context: Context, uri: Uri, database: IndexDatabase): Pair<Int, Int> {
        PDFBoxResourceLoader.init(context.applicationContext)
        val extracted = mutableListOf<Pair<Int, String>>()
        var totalPages = 0
        context.contentResolver.openInputStream(uri).use { stream ->
            requireNotNull(stream) { "Nie można otworzyć pliku PDF." }
            PDDocument.load(stream).use { document ->
                totalPages = document.numberOfPages
                val stripper = PDFTextStripper()
                for (page in 1..document.numberOfPages) {
                    stripper.startPage = page
                    stripper.endPage = page
                    val text = stripper.getText(document).trim()
                    if (text.isNotEmpty()) extracted += page to text
                }
            }
        }
        // Replace the previous index only after extraction completed successfully.
        database.replaceDocument(uri.toString(), extracted)
        return totalPages to extracted.size
    }
}
