package diptestbed.web.control

import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import diptestbed.database.services.{SoftwareService, UserService}
import diptestbed.domain.{DIPTestbedConfig, SoftwareId}
import diptestbed.protocol.WebResult._
import diptestbed.protocol.DomainCodecs._
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls._
import play.api.libs.Files
import play.api.mvc._
import scala.annotation.unused
import scala.concurrent.ExecutionContext
import scala.reflect.io.File
import scala.util.Try
import java.io.{BufferedInputStream, FileInputStream}

class ApiSoftwareController(
  val appConfig: DIPTestbedConfig,
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
    Action(parse.multipartFormData)(withRequestAuthn(_)((request, maybeUser) =>
      (for {
        user <- EitherT.fromEither[IO](
          maybeUser
            .leftMap(databaseErrorResult)
            .flatMap(_.toRight(authorizationErrorResult)))
        _ <- EitherT.fromEither[IO](Either.cond(
          user.canCreateSoftware, (), permissionErrorResult("Software access")))
        software <- EitherT.fromEither[IO](
            (request.body.file("software"), request.body.dataParts.get("name").flatMap(_.headOption))
              .tupled
              .toRight(Failure("Request must contain 'software' file and 'name' field")
              .withHttpStatus(BAD_REQUEST)))
        (softwareData, softwareName) = software
        sizedSoftwareData <- EitherT.fromEither[IO](Option
          .when(softwareData.ref.length() < maxBytes)(softwareData)
          .toRight(Failure("Request too large").withHttpStatus(BAD_REQUEST)))
        softwareBytes <- Try {
          val file = sizedSoftwareData.ref.toFile
          val bis = new BufferedInputStream(new FileInputStream(file))
          bis.readAllBytes()
        }.toEither
          .leftMap(error => Failure(s"Failed to read file stream: ${error}").withHttpStatus(INTERNAL_SERVER_ERROR))
          .toEitherT[IO]
        uploadMetaResult <-
          EitherT(softwareService.createSoftware(softwareName, user.id, isPublic = false, softwareBytes))
            .leftMap(databaseErrorResult)
            .map(meta => Success(meta).withHttpStatus(OK))
      } yield uploadMetaResult).merge).unsafeRunSync())

  def getSoftwareMetas: Action[AnyContent] =
    IOActionAny(withRequestAuthnOrFail(_)((_, user) =>
      for {
        result <- EitherT(softwareService.getSoftwareMetas(Some(user), write = false))
          .leftMap(databaseErrorResult)
          .map(softwareMetas => Success(softwareMetas).withHttpStatus(OK))
      } yield result
    ))

  def getSoftware(softwareId: SoftwareId): Action[AnyContent] =
    IOActionAny(withRequestAuthnOrFail(_)((_, user) =>
      for {
        software <- EitherT(softwareService.getSoftware(Some(user), softwareId, write = false)).leftMap(databaseErrorResult)
        existingSoftware <- EitherT.fromEither[IO](software.toRight(unknownIdErrorResult))
        result = {
            val tempFile = File.makeTemp()
            val writeStream = tempFile.bufferedOutput()
            writeStream.write(existingSoftware.content)
            writeStream.close()
            Ok.sendFile(
              tempFile.jfile,
              inline = true,
              fileName = _ => existingSoftware.meta.name.some,
              onClose = tempFile.delete)
        }
      } yield result
    ))
}
