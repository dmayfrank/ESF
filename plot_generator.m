

%% H2_Combined
clear
import_path = './Daten/Basismodell_16-18/XLSXs/';
% import plot data
y = readmatrix(append(import_path, 'H.xlsx'),'Range','B2');

limit_path = './Daten/Basismodell_16-18/XLSXs/HL.xlsx';
HL = readmatrix(limit_path,'Range','B2');

% create timeseries objects out of data
ts1 = timeseries(y(:, 1))/HL(1);
ts2 = timeseries(y(:, 2))/HL(2);
ts3 = timeseries(y(:, 3))/HL(3);

Legende = ["Germany - Capacity = 9.8 TWh","France - Capacity = 44.6 TWh","Netherlands - Capacity = 1.3 TWh"];

% format timeseries objects
ts1.TimeInfo.Units = 'hours';
ts1.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts1.TimeInfo.Format = 'mmm dd';       % Set format for display on x-axis.
ts1.Time = ts1.Time - ts1.Time(1);        % Express time relative to the start date.

ts2.TimeInfo.Units = 'hours';
ts2.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts2.TimeInfo.Format = 'mmm dd';       % Set format for display on x-axis.
ts2.Time = ts2.Time - ts2.Time(1);        % Express time relative to the start date.

ts3.TimeInfo.Units = 'hours';
ts3.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts3.TimeInfo.Format = 'mmm dd';           % Set format for display on x-axis.
ts3.Time = ts2.Time - ts2.Time(1);        % Express time relative to the start date.

% make plot
plot(ts1)
hold on
plot(ts2)
hold on
plot(ts3)

xlabel('Date');%,'FontSize',13)
ylabel('Normalized storage level') %,'FontSize',13)
ylim([0 1])
legend(Legende,'Location','best');%,'FontSize',12)
set(findall(gcf,'-property','FontSize'),'FontSize',11)
set(findall(gcf,'-property','Font'),'Font','Arial')



%% H2_RH
clear
import_path = './Daten/RH_16-18_correct/XLSXs/';
% import plot data
y = readmatrix(append(import_path, 'H.xlsx'),'Range','B2');

limit_path = './Daten/Basismodell_16-18/XLSXs/HL.xlsx';
HL = readmatrix(limit_path,'Range','B2');

% create timeseries objects out of data
ts1 = timeseries(y(:, 1))/HL(1);
ts2 = timeseries(y(:, 2))/HL(2);
ts3 = timeseries(y(:, 3))/HL(3);

Legende = ["Germany - Capacity = 9.8 TWh","France - Capacity = 44.6 TWh","Netherlands - Capacity = 1.3 TWh"];

% format timeseries objects
ts1.TimeInfo.Units = 'hours';
ts1.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts1.TimeInfo.Format = 'mmm dd';       % Set format for display on x-axis.
ts1.Time = ts1.Time - ts1.Time(1);        % Express time relative to the start date.

ts2.TimeInfo.Units = 'hours';
ts2.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts2.TimeInfo.Format = 'mmm dd';       % Set format for display on x-axis.
ts2.Time = ts2.Time - ts2.Time(1);        % Express time relative to the start date.

ts3.TimeInfo.Units = 'hours';
ts3.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts3.TimeInfo.Format = 'mmm dd';           % Set format for display on x-axis.
ts3.Time = ts2.Time - ts2.Time(1);        % Express time relative to the start date.

% make plot
plot(ts1)
hold on
plot(ts2)
hold on
plot(ts3)

xlabel('Date');%,'FontSize',13)
ylabel('Normalized storage level') %,'FontSize',13)
ylim([0 1])
legend(Legende,'Location','best');%,'FontSize',12)
set(findall(gcf,'-property','FontSize'),'FontSize',11)
set(findall(gcf,'-property','Font'),'Font','Arial')


%% 2d Electrolysis Power - Fuel Cell Power plot France - Combined
clear
import_path = './Daten/Basismodell_16-18/XLSXs/';
% import plot data
y1 = readmatrix(append(import_path, 'PtG.xlsx'),'Range','B2');
y2 = readmatrix(append(import_path, 'GtP.xlsx'),'Range','B2');

s1 = y1(:, 2)-y2(:, 2);
s1 = s1 ./ 1000; % change unit from MW to GW
s1 = flipud(s1); % flip to have january on top and december on bottom of y-axis

x = 1:24;
y = 1:365;
Z = reshape(s1, 365, 24);
[X,Y] = meshgrid(x,y);
surf(X,Y,Z, 'edgecolor','none')
colormap jet                        % <— Specify ‘colormap’ To Override Default 
colorbar
view(2)

% title('Hourly Electrolysis Power - Fuel Cell Power | France')
xlabel('Hour')
ylabel('Electrolysis Power - Fuel Cell Power [GW]')
%set(gca, 'Ytick',[16,76,136,196,256,317],'YTickLabel',{'January','March','May','July','September','November'});
set(gca, 'Ytick',[16,76,136,196,256,317]+30,'YTickLabel',{'November','September','July','May','March','January'});
set(gca, 'Xtick',[1,5,10,15,20,24]);


%% 2d Electrolysis Power - Fuel Cell Power plot France - RH
clear
import_path = './Daten/RH_16-18_correct/XLSXs/';
% import plot data
y1 = readmatrix(append(import_path, 'PtG.xlsx'),'Range','B2');
y2 = readmatrix(append(import_path, 'GtP.xlsx'),'Range','B2');

s1 = y1(:, 2)-y2(:, 2);
s1 = s1 ./ 1000; % change unit from MW to GW
s1 = flipud(s1); % flip to have january on top and december on bottom of y-axis

x = 1:24;
y = 1:365;
Z = reshape(s1, 365, 24);
[X,Y] = meshgrid(x,y);
surf(X,Y,Z, 'edgecolor','none')
colormap jet                        % <— Specify ‘colormap’ To Override Default 
colorbar
view(2)

% title('Hourly Electrolysis Power - Fuel Cell Power | France')
xlabel('Hour')
ylabel('Electrolysis Power - Fuel Cell Power [GW]')
%set(gca, 'Ytick',[16,76,136,196,256,317],'YTickLabel',{'January','March','May','July','September','November'});
set(gca, 'Ytick',[16,76,136,196,256,317]+30,'YTickLabel',{'November','September','July','May','March','January'});
set(gca, 'Xtick',[1,5,10,15,20,24]);

%% 1d Electrolysis Power plot - Combined
clear
import_path = './Daten/Basismodell_16-18/XLSXs/';
y = readmatrix(append(import_path, 'PtG.xlsx'),'Range','B2');

% create timeseries objects out of data
ts1 = timeseries(y(:, 1))./ 1000; % change unit from MW to GW
ts2 = timeseries(y(:, 2))./ 1000; % change unit from MW to GW
ts3 = timeseries(y(:, 3))./ 1000; % change unit from MW to GW

% format timeseries objects
ts1.TimeInfo.Units = 'hours';
ts1.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts1.TimeInfo.Format = 'mmm dd';           % Set format for display on x-axis.
ts1.Time = ts1.Time - ts1.Time(1);        % Express time relative to the start date.

ts2.TimeInfo.Units = 'hours';
ts2.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts2.TimeInfo.Format = 'mmm dd';           % Set format for display on x-axis.
ts2.Time = ts2.Time - ts2.Time(1);        % Express time relative to the start date.

ts3.TimeInfo.Units = 'hours';
ts3.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts3.TimeInfo.Format = 'mmm dd';           % Set format for display on x-axis.
ts3.Time = ts2.Time - ts2.Time(1);        % Express time relative to the start date.

% make plot
plot(ts1)
hold on
plot(ts2)
hold on
plot(ts3)

xlabel('Date')
ylabel('Electrolysis Power [GW]')
legend(["Germany","France","Netherlands"],'Location','best')

%% 1d Electrolysis Power plot - RH
clear
import_path = './Daten/RH_16-18_correct/XLSXs/';
y = readmatrix(append(import_path, 'PtG.xlsx'),'Range','B2');

% create timeseries objects out of data
ts1 = timeseries(y(:, 1))./ 1000; % change unit from MW to GW
ts2 = timeseries(y(:, 2))./ 1000; % change unit from MW to GW
ts3 = timeseries(y(:, 3))./ 1000; % change unit from MW to GW

% format timeseries objects
ts1.TimeInfo.Units = 'hours';
ts1.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts1.TimeInfo.Format = 'mmm dd';           % Set format for display on x-axis.
ts1.Time = ts1.Time - ts1.Time(1);        % Express time relative to the start date.

ts2.TimeInfo.Units = 'hours';
ts2.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts2.TimeInfo.Format = 'mmm dd';           % Set format for display on x-axis.
ts2.Time = ts2.Time - ts2.Time(1);        % Express time relative to the start date.

ts3.TimeInfo.Units = 'hours';
ts3.TimeInfo.StartDate = '01-Jan-2030';   % Set start date.
ts3.TimeInfo.Format = 'mmm dd';           % Set format for display on x-axis.
ts3.Time = ts2.Time - ts2.Time(1);        % Express time relative to the start date.

% make plot
plot(ts1)
hold on
plot(ts2)
hold on
plot(ts3)

xlabel('Date')
ylabel('Electrolysis Power [GW]')
legend(["Germany","France","Netherlands"],'Location','best')

