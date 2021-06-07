package iotfrisbee.database.services

import java.time.ZonedDateTime
import java.util.UUID
import scala.concurrent.ExecutionContext
import cats.effect.Async
import cats.implicits._
import iotfrisbee.database.catalog.DiskGolfBasketCatalog.DiskGolfBasketTable
import iotfrisbee.database.catalog.DiskGolfDiskCatalog.DiskGolfDiskTable
import iotfrisbee.database.catalog.DiskGolfGameStageCatalog.DiskGolfGameStageTable
import iotfrisbee.database.catalog.DiskGolfTrackCatalog.DiskGolfTrackTable
import iotfrisbee.database.catalog.HardwareCatalog.HardwareTable
import iotfrisbee.database.catalog.UserCatalog.UserTable
import iotfrisbee.database.catalog.DiskGolfGameCatalog.{
  DiskGolfGameRow,
  DiskGolfGameTable,
  toDomain => diskGolfGameToDomain,
}
import iotfrisbee.database.driver.DatabaseDriver.existsOrError
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult
import iotfrisbee.database.services.DiskGolfGameService._
import iotfrisbee.domain._
import slick.dbio.DBIOAction.sequenceOption

class DiskGolfGameService[F[_]: Async](
  val userTable: UserTable,
  val diskGolfTrackTable: DiskGolfTrackTable,
  val diskGolfDiskTable: DiskGolfDiskTable,
  val diskGolfBasketTable: DiskGolfBasketTable,
  val diskGolfGameTable: DiskGolfGameTable,
  val diskGolfGameStageTable: DiskGolfGameStageTable,
  val hardwareTable: HardwareTable,
)(implicit executionContext: ExecutionContext) {
  import diskGolfGameTable._
  import diskGolfGameTable.dbDriver.profile.api._
  import diskGolfDiskTable.DiskGolfDiskQuery
  import diskGolfTrackTable.DiskGolfTrackQuery

  import userTable.UserQuery

  def countDiskGolfGames(): F[DatabaseResult[Int]] =
    DiskGolfGameQuery.length.result.tryRunDBIO(dbDriver)

  def createDiskGolfGame(
    name: String,
    diskId: DiskGolfDiskId,
    playerId: UserId,
  ): F[DatabaseResult[Either[List[DiskGolfGameCreationError], DiskGolfGame]]] = {
    val row =
      DiskGolfGameRow(
        name = name,
        diskUUID = diskId.value,
        playerUUID = playerId.value,
      )

    val inProgressGameDiskCheck: DBIOAction[Option[UUID], NoStream, Effect.Read] =
      DiskGolfGameQuery
        .filter(game => game.diskUUID === diskId.value && !game.finished)
        .map(_.uuid)
        .result
        .headOption

    val diskCheck: DBIOAction[Option[UUID], NoStream, Effect.Read] =
      DiskGolfDiskQuery
        .filter(_.uuid === diskId.value)
        .map(_.uuid)
        .result
        .headOption

    val playerCheck: DBIOAction[Option[UUID], NoStream, Effect.Read] =
      UserQuery
        .filter(_.uuid === playerId.value)
        .map(_.uuid)
        .result
        .headOption

    val diskGolfGame
      : DBIOAction[Either[List[DiskGolfGameCreationError], Int], NoStream, Effect.Read with Effect.Write] =
      for {
        existenceDiskError <- existsOrError(diskCheck, NonExistentDisk)
        existencePlayerError <- existsOrError(playerCheck, NonExistentPlayer)
        existanceInProgressGameDisk <-
          inProgressGameDiskCheck
            .map(_.map(_ => NonExistentFreeDisk))
            .map(_.filter(_ => existencePlayerError.isEmpty))
        existenceErrors = (existenceDiskError :: existencePlayerError :: existanceInProgressGameDisk :: Nil).flatten
        createdGame <-
          sequenceOption(Option.when(existenceErrors.isEmpty)(DiskGolfGameQuery += row)).map(_.toRight(existenceErrors))
      } yield createdGame

    diskGolfGame
      .tryRunDBIO(dbDriver)
      .map(_.map(_.map(_ => diskGolfGameToDomain(row))))
  }

  def startDiskGolfGame(gameId: DiskGolfGameId): F[DatabaseResult[Option[DiskGolfGame]]] = {
    val startableGame = DiskGolfGameQuery
      .filter(game => game.uuid === gameId.value && !game.startTimestamp.isDefined && !game.finished)

    val startedGame =
      for {
        gameAndTimeZone <-
          startableGame
            .joinLeft(DiskGolfDiskQuery)
            .on { case (g, d) => g.diskUUID === d.uuid }
            .joinLeft(DiskGolfTrackQuery)
            .on { case ((_, d), t) => d.flatMap[Boolean](_.trackUUID.? === t.uuid) }
            .map { case ((game, _), track) => track.map(t => (game, t.timezone)) }
            .result
            .headOption
            .map(_.flatten)
            .map(_.map { case (game, timezone) => (game, DomainTimeZoneId.fromString(timezone).toOption.get) })
        updatedGame <- sequenceOption(gameAndTimeZone.map {
          case (game, timezone) =>
            val timestampNow = Some(ZonedDateTime.now(timezone.zone.value).toString)
            startableGame
              .map(_.startTimestamp)
              .update(timestampNow)
              .map(_ => game.copy(startTimestamp = timestampNow))
        })
      } yield updatedGame

    startedGame
      .tryRunDBIO(dbDriver)
      .map(_.map(_.map(row => diskGolfGameToDomain(row))))
  }

  def finishDiskGolfGame(gameId: DiskGolfGameId): F[DatabaseResult[Option[DiskGolfGame]]] = {
    val finishableGameQuery = DiskGolfGameQuery
      .filter(game => game.uuid === gameId.value && game.startTimestamp.isDefined && !game.finished)

    val finishedGame =
      for {
        finishableGame <- finishableGameQuery.result.headOption
        updatedGame <- sequenceOption(
          finishableGame.map(game =>
            finishableGameQuery.map(_.finished).update(true).map(_ => game.copy(finished = true)),
          ),
        )
      } yield updatedGame

    finishedGame
      .tryRunDBIO(dbDriver)
      .map(_.map(_.map(row => diskGolfGameToDomain(row))))
  }

  def getDiskGolfGame(id: DiskGolfGameId): F[DatabaseResult[Option[DiskGolfGame]]] =
    DiskGolfGameQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(diskGolfGameToDomain))
      .tryRunDBIO(dbDriver)

  def getDiskGolfGames: F[DatabaseResult[Seq[DiskGolfGame]]] =
    DiskGolfGameQuery.result
      .map(_.map(diskGolfGameToDomain))
      .tryRunDBIO(dbDriver)

}

object DiskGolfGameService {
  sealed trait DiskGolfGameCreationError
  case object NonExistentDisk extends DiskGolfGameCreationError
  case object NonExistentPlayer extends DiskGolfGameCreationError
  case object NonExistentFreeDisk extends DiskGolfGameCreationError
}
