package diptestbed.web.control

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits.toTraverseOps
import diptestbed.database.services.{HardwareService, SoftwareService, UserService}
import diptestbed.domain.{DIPTestbedConfig, SoftwareId, SoftwareMeta, User}
import diptestbed.web.control.FormHelper.optionalBoolean
import diptestbed.web.ioControls.IOController
import play.api.data.Form
import play.api.data.Forms.{text, tuple}
import play.api.i18n.Messages
import play.api.mvc._

import java.util.UUID
import scala.util.Try

class AppSoftwareController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val softwareService: SoftwareService[IO],
  val userService: UserService[IO]
)(implicit
  iort: IORuntime,
  messages: Messages
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {
  implicit val ac: DIPTestbedConfig = appConfig
  def setPublic(
    sessionUser: User,
    softwareId: String,
    isPublic: Boolean
  ): Boolean =
    Try(UUID.fromString(softwareId)).toOption.map(SoftwareId(_))
      .traverse(id =>
        softwareService.setPublic(Some(sessionUser), id, isPublic)).value.map(_.toOption.isDefined).unsafeRunSync()

  def publicForm(sessionUser: User): Form[(String, Boolean)] = Form[(String, Boolean)](
    tuple(
      "software_id" -> text,
      "is_public" -> optionalBoolean,
    ) verifying ("Failed to change permissions", {
      case (softwareId, isPublic) =>
        setPublic(sessionUser, softwareId, isPublic)
    })
  )

  def dbSoftware(sessionUser: User): IO[List[SoftwareMeta]] =
    softwareService.getSoftwareMetas(Some(sessionUser), write = false)
      .map(_.toOption.sequence.flatten.toList)

  def list: Action[AnyContent] =
    Action { implicit r =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, user) =>
        Ok(diptestbed.web.views.html.softwareList(
          appConfig, Some(user), dbSoftware(user).unsafeRunSync(), publicForm(user)))
      }.unsafeRunSync()
    }

  def publicRequest: Action[AnyContent] =
    Action { implicit request =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, user) =>
        publicForm(user).bindFromRequest.fold(
          formWithErrors => BadRequest(diptestbed.web.views.html.softwareList(
            appConfig, Some(user), dbSoftware(user).unsafeRunSync(), formWithErrors)),
          _ => Ok(diptestbed.web.views.html.softwareList(
            appConfig, Some(user), dbSoftware(user).unsafeRunSync(), publicForm(user)))
        )
      }.unsafeRunSync()
    }

}
