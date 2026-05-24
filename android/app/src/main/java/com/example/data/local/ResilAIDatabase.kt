package com.example.data.local

import android.content.Context
import androidx.room.*
import com.example.data.model.AssessmentSummaryEntity
import com.example.data.model.FindingEntity

@Dao
interface ResilAIDao {
    @Query("SELECT * FROM assessment_summary WHERE id = :id")
    suspend fun getAssessmentSummary(id: String): AssessmentSummaryEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAssessmentSummary(summary: AssessmentSummaryEntity)

    @Query("SELECT * FROM findings")
    suspend fun getAllFindings(): List<FindingEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertFindings(findings: List<FindingEntity>)

    @Query("DELETE FROM findings")
    suspend fun deleteAllFindings()
}

@Database(entities = [AssessmentSummaryEntity::class, FindingEntity::class], version = 1)
abstract class ResilAIDatabase : RoomDatabase() {
    abstract fun dao(): ResilAIDao

    companion object {
        @Volatile
        private var INSTANCE: ResilAIDatabase? = null

        fun getDatabase(context: Context): ResilAIDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    ResilAIDatabase::class.java,
                    "resilai_database"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
