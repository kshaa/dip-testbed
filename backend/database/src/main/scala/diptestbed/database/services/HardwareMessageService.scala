package diptestbed.database.services

import scala.concurrent.ExecutionContext
import cats.effect.Async
import cats.implicits._
import io.circe.Json
import diptestbed.database.catalog.HardwareCatalog.HardwareTable
import diptestbed.database.catalog.HardwareMessageCatalog.{
  HardwareMessageRow,
  HardwareMessageTable,
  toDomain => hardwareMessageToDomain,
}
import diptestbed.database.driver.DatabaseDriverOps._
import diptestbed.database.driver.DatabaseOutcome.DatabaseResult
import diptestbed.domain.{HardwareId, HardwareMessage, HardwareMessageId}
import slick.dbio.DBIOAction.sequenceOption

class HardwareMessageService[F[_]: Async](
  val hardwareMessageTable: HardwareMessageTable,
  val hardwareTable: HardwareTable,
)(implicit executionContext: ExecutionContext) {
  import hardwareMessageTable.dbDriver.profile.api._
  import hardwareMessageTable._
  import hardwareTable.HardwareQuery

  def countHardwareMessage(): F[DatabaseResult[Int]] =
    HardwareMessageQuery.length.result.tryRunDBIO(dbDriver)

  def createHardwareMessage(
    messageType: String,
    message: Json,
    hardwareId: HardwareId,
  ): F[DatabaseResult[Option[HardwareMessage]]] = {
    val row = HardwareMessageRow(messageType = messageType, message = message.noSpaces, hardwareId = hardwareId.value)
    val hardwareMessageCreation: DBIOAction[Option[Int], NoStream, Effect.Read with Effect.Write] =
      for {
        existingHardware <- HardwareQuery.filter(_.uuid === hardwareId.value).result.headOption
        hardwareMessageCreation <- sequenceOption(Option.when(existingHardware.isDefined)(HardwareMessageQuery += row))
      } yield hardwareMessageCreation

    hardwareMessageCreation
      .tryRunDBIO(dbDriver)
      .map(_.map(_.map(_ => hardwareMessageToDomain(row))))
  }

  def getHardwareMessage(id: HardwareMessageId): F[DatabaseResult[Option[HardwareMessage]]] =
    HardwareMessageQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(hardwareMessageToDomain))
      .tryRunDBIO(dbDriver)

  def getHardwareMessages(hardwareId: Option[HardwareId]): F[DatabaseResult[Seq[HardwareMessage]]] =
    HardwareMessageQuery
      .filterOpt(hardwareId)(_.hardwareUuid === _.value)
      .result
      .map(_.map(hardwareMessageToDomain))
      .tryRunDBIO(dbDriver)

}
