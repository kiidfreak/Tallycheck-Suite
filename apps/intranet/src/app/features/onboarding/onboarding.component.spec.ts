import { ComponentFixture, TestBed } from '@angular/core/testing';
import { OnboardingComponent } from './onboarding.component';
import { AuthService } from '@omni/auth';
import { Component, Input } from '@angular/core';
import { IconComponent } from '@omni/ui';
import { throwError, Subject } from 'rxjs';

@Component({
  // eslint-disable-next-line @angular-eslint/component-selector
  selector: 'omni-icon',
  standalone: true,
  template: '<span>mock icon</span>'
})
class MockIconComponent {
  @Input() name!: string;
}

describe('OnboardingComponent', () => {
  let component: OnboardingComponent;
  let fixture: ComponentFixture<OnboardingComponent>;
  let mockAuthService: { register_user: jest.Mock };
  let registerSubject: Subject<unknown>;

  beforeEach(async () => {
    registerSubject = new Subject<unknown>();
    mockAuthService = {
      // Mock register_user to return a fake successful RxJS Observable
      register_user: jest.fn().mockReturnValue(registerSubject.asObservable()) 
    };

    await TestBed.configureTestingModule({
      imports: [OnboardingComponent],
      providers: [
        { provide: AuthService, useValue: mockAuthService }
      ]
    })
    .overrideComponent(OnboardingComponent, {
      remove: { imports: [IconComponent] },
      add: { imports: [MockIconComponent] }
    })
    .compileComponents();

    fixture = TestBed.createComponent(OnboardingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the onboarding component successfully', () => {
    expect(component).toBeTruthy();
  });

  it('should block submission and show an error if fields are empty', () => {
    component.first_name = '';
    component.last_name = '';
    component.submit();
    
    expect(component.error()).toEqual('Please fill out all fields.');
    expect(mockAuthService.register_user).not.toHaveBeenCalled();
  });

  it('should show a loading state and hit the backend when valid data is submitted', () => {
    component.first_name = 'John';
    component.last_name = 'Doe';
    component.submit();
    
    expect(component.busy()).toBe(true); 
    expect(mockAuthService.register_user).toHaveBeenCalledWith('John', 'Doe', 'standard', '7am-5pm', undefined, undefined);
  });

  it('should validate custom shift times to be exactly 10 hours', () => {
    component.first_name = 'John';
    component.last_name = 'Doe';
    component.shift_hours = 'custom';
    component.custom_shift_start = '08:00';
    component.custom_shift_end = '17:00'; // 9 hours
    component.submit();

    expect(component.error()).toEqual('Custom shift must be exactly 10 hours.');
    expect(mockAuthService.register_user).not.toHaveBeenCalled();

    // Now set valid 10 hours
    component.custom_shift_end = '18:00'; // 10 hours
    component.submit();

    expect(component.busy()).toBe(true);
    expect(mockAuthService.register_user).toHaveBeenCalledWith('John', 'Doe', 'standard', 'custom', '08:00', '18:00');
  });

  it('should turn off loading and show an error message if the backend crashes', () => {
    // Force the fake AuthService to throw an error for this one test
    mockAuthService.register_user.mockReturnValueOnce(throwError(() => new Error('Backend crash')));
    
    component.first_name = 'John';
    component.last_name = 'Doe';
    component.submit();
    
    expect(component.error()).toEqual('Failed to register. Please try again.');
    expect(component.busy()).toBe(false); 
  });
});
