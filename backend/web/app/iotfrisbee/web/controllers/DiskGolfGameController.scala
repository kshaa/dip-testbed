package iotfrisbee.web.controllers

import scala.annotation.unused
import scala.concurrent.ExecutionContext
import play.api.mvc._
import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import iotfrisbee.database.services.DiskGolfGameService
import iotfrisbee.domain.DiskGolfGameId
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.protocol._
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._

class DiskGolfGameController(
  val cc: ControllerComponents,
  val diskGolfGameService: DiskGolfGameService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController {

  def createDiskGolfGame: Action[CreateDiskGolfGame] = {
    IOActionJSON[CreateDiskGolfGame] { request =>
      EitherT(
        diskGolfGameService.createDiskGolfGame(request.body.name, request.body.diskId, request.body.playerId),
      ).leftMap(databaseError => Failure(databaseError.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(creation =>
          EitherT.fromEither(
            creation
              .leftMap(_.map {
                case DiskGolfGameService.NonExistentDisk     => "Disk with that id doesn't exist"
                case DiskGolfGameService.NonExistentPlayer   => "Player with that id doesn't exist"
                case DiskGolfGameService.NonExistentFreeDisk => "Disk with that id has an active game in progress"
              })
              .bimap(
                errorMessages => Failure(errorMessages).withHttpStatus(BAD_REQUEST),
                diskGolfGame => Success(diskGolfGame).withHttpStatus(OK),
              ),
          ),
        )
    }
  }

  def startDiskGolfGame(diskGolfGameId: DiskGolfGameId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfGameService.startDiskGolfGame(diskGolfGameId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("A startable disk golf game with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                startedDiskGolfGame => Success(startedDiskGolfGame).withHttpStatus(OK),
              ),
          ),
        )
    }

  def finishDiskGolfGame(diskGolfGameId: DiskGolfGameId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfGameService.finishDiskGolfGame(diskGolfGameId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("A finishable disk golf game with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                finishedDiskGolfGame => Success(finishedDiskGolfGame).withHttpStatus(OK),
              ),
          ),
        )
    }

  def getDiskGolfGames: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfGameService.getDiskGolfGames)
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          diskGolfGames => Success(diskGolfGames).withHttpStatus(OK),
        )
    }

  def getDiskGolfGame(diskGolfGameId: DiskGolfGameId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfGameService.getDiskGolfGame(diskGolfGameId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("Disk golf game with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                diskGolfGame => Success(diskGolfGame).withHttpStatus(OK),
              ),
          ),
        )
    }
}
