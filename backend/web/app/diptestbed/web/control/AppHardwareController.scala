package diptestbed.web.control

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits.toTraverseOps
import diptestbed.database.services.{HardwareService, UserService}
import diptestbed.domain.{DIPTestbedConfig, Hardware, HardwareId, User}
import diptestbed.web.control.FormHelper.optionalBoolean
import diptestbed.web.ioControls.IOController
import play.api.data.Form
import play.api.data.Forms.{text, tuple}
import play.api.i18n.Messages
import play.api.mvc._
import java.util.UUID
import scala.util.Try

class AppHardwareController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val hardwareService: HardwareService[IO],
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
    hardwareId: String,
    isPublic: Boolean
  ): Boolean =
    Try(UUID.fromString(hardwareId)).toOption.map(HardwareId)
      .traverse(id =>
        hardwareService.setPublic(Some(sessionUser), id, isPublic)).value.map(_.toOption.isDefined).unsafeRunSync()

  def publicForm(sessionUser: User): Form[(String, Boolean)] = Form[(String, Boolean)](
    tuple(
      "hardware_id" -> text,
      "is_public" -> optionalBoolean,
    ) verifying ("Failed to change permissions", {
      case (hardwareId, isPublic) =>
        setPublic(sessionUser, hardwareId, isPublic)
    })
  )

  def dbHardware(sessionUser: User): IO[List[Hardware]] =
    hardwareService.getHardwares(Some(sessionUser), write = false)
      .map(_.toOption.sequence.flatten.toList)

  def list: Action[AnyContent] =
    Action { implicit request =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, user) =>
        Ok(diptestbed.web.views.html.hardwareList(
          appConfig, Some(user), dbHardware(user).unsafeRunSync(), publicForm(user)))
      }.unsafeRunSync()
    }

  def publicRequest: Action[AnyContent] =
    Action { implicit request =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, user) =>
        publicForm(user).bindFromRequest.fold(
          formWithErrors => BadRequest(diptestbed.web.views.html.hardwareList(
            appConfig, Some(user), dbHardware(user).unsafeRunSync(), formWithErrors)),
          _ => Ok(diptestbed.web.views.html.hardwareList(
            appConfig, Some(user), dbHardware(user).unsafeRunSync(), publicForm(user)))
        )
      }.unsafeRunSync()
    }
}
