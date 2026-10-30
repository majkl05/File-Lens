package com.filelens.android

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { FileLensScreen() }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun FileLensScreen() {
    val context = LocalContext.current
    val database = remember { IndexDatabase(context.applicationContext) }
    val scope = rememberCoroutineScope()
    var query by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Wybierz dokumenty PDF, aby rozpocząć.") }
    var busy by remember { mutableStateOf(false) }
    var pageCount by remember { mutableIntStateOf(database.indexedPageCount()) }
    var hits by remember { mutableStateOf(emptyList<SearchHit>()) }

    val picker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenMultipleDocuments()
    ) { uris: List<Uri> ->
        if (uris.isNotEmpty()) scope.launch {
            busy = true
            var indexed = 0
            var textPages = 0
            val errors = mutableListOf<String>()
            withContext(Dispatchers.IO) {
                uris.forEach { uri ->
                    try {
                        context.contentResolver.takePersistableUriPermission(
                            uri, Intent.FLAG_GRANT_READ_URI_PERMISSION
                        )
                        val result = PdfIndexer.index(context, uri, database)
                        indexed++
                        textPages += result.second
                    } catch (error: Exception) {
                        errors += displayName(context, uri) + ": " +
                            (error.message ?: "błąd odczytu")
                    }
                }
            }
            pageCount = database.indexedPageCount()
            status = "Przetworzono: $indexed PDF, $textPages stron z tekstem." +
                if (errors.isNotEmpty()) "\nBłędy: " + errors.joinToString("; ") else ""
            busy = false
        }
    }

    MaterialTheme {
        Scaffold(topBar = { TopAppBar(title = { Text("FileLens") }) }) { padding ->
            Column(
                Modifier.fillMaxSize().padding(padding).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text("Lokalna wyszukiwarka dokumentów PDF")
                Button(
                    onClick = { picker.launch(arrayOf("application/pdf")) },
                    enabled = !busy, modifier = Modifier.fillMaxWidth()
                ) { Text("Dodaj i indeksuj PDF") }
                if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
                Text(status, style = MaterialTheme.typography.bodySmall)
                Text("Zaindeksowane strony: $pageCount")
                OutlinedTextField(
                    value = query, onValueChange = { query = it },
                    label = { Text("Szukaj słów (AND)") },
                    modifier = Modifier.fillMaxWidth(), singleLine = true
                )
                Button(
                    onClick = {
                        scope.launch {
                            hits = withContext(Dispatchers.IO) { database.search(query) }
                            status = "Znaleziono " + hits.size + " pasujących stron."
                        }
                    },
                    enabled = query.isNotBlank() && !busy,
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Szukaj") }
                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(hits) { hit ->
                        Card(Modifier.fillMaxWidth().clickable {
                            try {
                                val intent = Intent(Intent.ACTION_VIEW).apply {
                                    setDataAndType(Uri.parse(hit.uri), "application/pdf")
                                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                }
                                context.startActivity(intent)
                            } catch (_: Exception) {
                                status = "Brak aplikacji do otwierania PDF."
                            }
                        }) {
                            Column(Modifier.padding(12.dp)) {
                                Text(displayName(context, Uri.parse(hit.uri)) + " — strona " + hit.page)
                                Text(hit.snippet, style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }
        }
    }
}

private fun displayName(context: android.content.Context, uri: Uri): String = try {
    context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
        ?.use { cursor ->
            if (cursor.moveToFirst()) cursor.getString(0) else uri.lastPathSegment ?: "PDF"
        } ?: (uri.lastPathSegment ?: "PDF")
} catch (_: Exception) { uri.lastPathSegment ?: "PDF" }
