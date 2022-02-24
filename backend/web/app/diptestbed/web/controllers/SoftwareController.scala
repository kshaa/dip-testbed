package diptestbed.web.controllers

import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import diptestbed.database.services.{SoftwareService, UserService}
import diptestbed.domain.SoftwareId
import diptestbed.protocol.Codecs._
import diptestbed.protocol.WebResult._
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls._
import play.api.libs.Files
import play.api.mvc._
import scala.annotation.unused
import scala.concurrent.ExecutionContext
import scala.reflect.io.File
import scala.util.Try
import java.io.{FileInputStream, BufferedInputStream}

class SoftwareController(
  val cc: ControllerComponents,
  val softwareService: SoftwareService[IO],
  val userService: UserService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController
    with AuthController[IO]
    with ResultsController[IO] {
  val maxBytes = 5242880L // 5 MiB

  def createSoftware: Action[MultipartFormData[Files.TemporaryFile]] =
    Action(parse.multipartFormData)(withRequestAuthn(_)((request, maybeUser) => {
      val authWithSoftwareData = EitherT.fromEither[IO](
        maybeUser
          .leftMap(databaseErrorResult)
          .flatMap(_.toRight(authorizationErrorResult))
          .flatMap(user => {
            println(request.body.file("software"), request.body.dataParts.get("name"))
            (request.body.file("software"), request.body.dataParts.get("name").flatMap(_.headOption)).tupled
              .toRight(Failure("Request must contain 'software' file and 'name' field").withHttpStatus(BAD_REQUEST))
              .flatMap {
                case (data, name) =>
                  Option
                    .when(data.ref.length() < maxBytes)(data)
                    .toRight(
                      Failure("Request too large").withHttpStatus(BAD_REQUEST),
                    )
                    .map(_ => (data, name, user))
              }
          })
      )

      val authWithSoftwareBytes = authWithSoftwareData.flatMap {
        case (data, name, user) =>
          Try {
            val file = data.ref.toFile
            val bis = new BufferedInputStream(new FileInputStream(file))
            bis.readAllBytes()
          }.toEither
            .leftMap(error => Failure(s"Failed to read file stream: ${error}").withHttpStatus(INTERNAL_SERVER_ERROR))
            .toEitherT[IO]
            .map((_, name, user))
      }

      val pipeline = authWithSoftwareBytes.flatMap {
        case (bytes, name, user) =>
          EitherT(softwareService.createSoftware(name, user.id, bytes))
            .leftMap(databaseErrorResult)
            .map(meta => Success(meta).withHttpStatus(OK))
      }

      pipeline.merge
    }).unsafeRunSync())

  def getSoftwareMetas: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(softwareService.getSoftwareMetas)
        .leftMap(databaseErrorResult)
        .map(softwareMetas => Success(softwareMetas).withHttpStatus(OK))
    }

  def getSoftware(softwareId: SoftwareId): Action[AnyContent] =
    Action {
      EitherT(softwareService.getSoftware(softwareId))
        .leftMap(databaseErrorResult)
        .subflatMap(_.toRight(unknownIdErrorResult))
        .map(software => {
          val tempFile = File.makeTemp()
          val writeStream = tempFile.bufferedOutput()
          writeStream.write(software.content)
          writeStream.close()
          Ok.sendFile(tempFile.jfile, inline = true, fileName = _ => software.meta.name.some, onClose = tempFile.delete)
        })
        .merge
        .unsafeRunSync()
    }
}
